import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
from typing import Dict, List, Tuple, Any, Optional
import logging
from pal.core.models import Student, Topic, Resource, KnowledgeState
from pal.knowledge_graph.models import KnowledgeGraph, GraphEdge
from pal.ml_models.ml.django_data_preparation import DjangoDataPreparation

logger = logging.getLogger(__name__)


class AdaptiveLearningPathLSTM(nn.Module):
    """
    LSTM model for generating adaptive learning paths.
    integrates with django models and knowledge graph stuff
    """
    
    def __init__(self, num_topics: int, hidden_size: int = 128, num_layers: int = 2, 
                 dropout: float = 0.3):
        """
        init the LSTM model
        
        Args:
            num_topics: how many topics we got in the system
            hidden_size: lstm hidden size  
            num_layers: how many lstm layers to stack
            dropout: dropout rate to prevent overfitting
        """
        super(AdaptiveLearningPathLSTM, self).__init__()
        
        
        self.num_topics = num_topics
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # encode student profile into vector 
        self.student_encoder = nn.Linear(10, hidden_size)  # 10 features for now
        
        # encode topic mastery scores  
        self.mastery_encoder = nn.Linear(num_topics, hidden_size)
        
        # input size = mastery + student + topic one-hot
        input_size = hidden_size * 2 + num_topics
        
        # main LSTM for sequence modeling
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # attention mechanism for topic importance weighting  
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=4, dropout=dropout)
        
        # memory network for prerequisite relationships
        self.memory_keys = nn.Parameter(torch.randn(num_topics, hidden_size))
        self.memory_values = nn.Parameter(torch.randn(num_topics, hidden_size))
        
        # generate next topic probabilities
        self.path_generator = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, num_topics),
            nn.Softmax(dim=-1)
        )
        
        # predict difficulty level
        self.difficulty_predictor = nn.Linear(hidden_size, 3)  # beginner, intermediate, advanced
        
        # estimate learning time
        self.time_estimator = nn.Linear(hidden_size, 1)
        
        self.dropout = nn.Dropout(dropout)
    
    def encode_student_profile(self, student_features: torch.Tensor) -> torch.Tensor:
        """
        encode student features into hidden representation
        
        Args:
            student_features: tensor of student features [batch_size, 10]
            
        Returns:
            encoded student profile [batch_size, hidden_size]
        """
        return self.student_encoder(student_features)
    
    def encode_mastery_state(self, mastery_scores: torch.Tensor) -> torch.Tensor:
        """
        encode current mastery state
        
        Args:
            mastery_scores: mastery scores for all topics [batch_size, num_topics]
            
        Returns:
            encoded mastery state [batch_size, hidden_size]
        """
        return self.mastery_encoder(mastery_scores)
    
    def forward(self, student_features: torch.Tensor, mastery_scores: torch.Tensor,
                topic_sequence: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        forward pass thru the model
        
        Args:
            student_features: student profile [batch_size, 10]
            mastery_scores: current mastery [batch_size, num_topics]
            topic_sequence: sequence of topics [batch_size, seq_len, num_topics]
            
        Returns:
            dict with predictions
        """
        batch_size, seq_len, _ = topic_sequence.shape
        
        # encode inputs
        student_encoded = self.encode_student_profile(student_features)  # [batch_size, hidden_size]
        mastery_encoded = self.encode_mastery_state(mastery_scores)      # [batch_size, hidden_size]
        
        # expand to sequence length
        student_seq = student_encoded.unsqueeze(1).expand(-1, seq_len, -1)  # [batch_size, seq_len, hidden_size]
        mastery_seq = mastery_encoded.unsqueeze(1).expand(-1, seq_len, -1)   # [batch_size, seq_len, hidden_size]
        
        # concat all inputs  
        combined_input = torch.cat([student_seq, mastery_seq, topic_sequence], dim=-1)
        
        # pass thru LSTM
        lstm_out, (hidden, cell) = self.lstm(combined_input)
        lstm_out = self.dropout(lstm_out)
        
        # apply attention
        lstm_out_transposed = lstm_out.transpose(0, 1)  # [seq_len, batch_size, hidden_size]
        attended_out, attention_weights = self.attention(
            lstm_out_transposed, lstm_out_transposed, lstm_out_transposed
        )
        attended_out = attended_out.transpose(0, 1)  # [batch_size, seq_len, hidden_size]
        
        # generate predictions
        next_topic_probs = self.path_generator(attended_out)  # [batch_size, seq_len, num_topics]
        difficulty_preds = self.difficulty_predictor(attended_out)  # [batch_size, seq_len, 3]
        time_estimates = self.time_estimator(attended_out)  # [batch_size, seq_len, 1]
        
        return {
            'next_topic_probs': next_topic_probs,
            'difficulty_preds': difficulty_preds,
            'time_estimates': time_estimates,
            'attention_weights': attention_weights,
            'hidden_state': hidden
        }
    
    def predict_next_topics(self, student_features: torch.Tensor, mastery_scores: torch.Tensor,
                           num_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        predict next topics for student
        
        Args:
            student_features: student features [10]
            mastery_scores: current mastery scores [num_topics]
            num_recommendations: how many topics to recommend
            
        Returns:
            list of topic recommendations with metadata
        """
        self.eval()
        
        with torch.no_grad():
            # add batch dimension
            student_features = student_features.unsqueeze(0)  # [1, 10]
            mastery_scores = mastery_scores.unsqueeze(0)      # [1, num_topics]
            
            # create dummy topic sequence (only need final prediction) 
            topic_sequence = torch.zeros(1, 1, self.num_topics)  # [1, 1, num_topics]
            
            # forward pass
            outputs = self.forward(student_features, mastery_scores, topic_sequence)
            
            # get predictions for last time step
            topic_probs = outputs['next_topic_probs'][0, -1, :]  # [num_topics]
            difficulty_probs = F.softmax(outputs['difficulty_preds'][0, -1, :], dim=-1)  # [3]
            time_estimate = outputs['time_estimates'][0, -1, 0].item()  # scalar
            
            # get top recommendations
            top_indices = torch.topk(topic_probs, num_recommendations).indices
            
            recommendations = []
            for idx in top_indices:
                topic_idx = idx.item()
                recommendations.append({
                    'topic_id': topic_idx,
                    'confidence': topic_probs[topic_idx].item(),
                    'difficulty_probs': {
                        'beginner': difficulty_probs[0].item(),
                        'intermediate': difficulty_probs[1].item(),
                        'advanced': difficulty_probs[2].item()
                    },
                    'estimated_time_hours': max(0.5, time_estimate)  # atleast 30 mins
                })
            
            return recommendations


class DjangoIntegratedPathGenerator:
    """
    django integrated learning path generator.
    combines lstm with knowledge graph stuff
    """
    
    def __init__(self):
        self.data_prep = DjangoDataPreparation()
        self.num_topics = self.data_prep.get_num_topics()
        self.topic_list = self.data_prep.get_topic_list()
        self.current_course = None
        self.current_observed_topic_indices = set()
        self.current_topics = []
        self.current_topic_to_index = {}
        
        # init LSTM model
        self.lstm_model = AdaptiveLearningPathLSTM(self.num_topics)
        
        # load pretrained model if we have one
        self._load_model_if_exists()
    
    def _load_model_if_exists(self):
        """load pretrained model if it exists"""
        model_path = 'trained_models/adaptive_path_lstm.pth'
        try:
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location='cpu')
                if 'model_state_dict' in checkpoint:
                    self.lstm_model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.lstm_model.load_state_dict(checkpoint)
                logger.info("loaded pretrained adaptive path LSTM model")
        except Exception as e:
            logger.warning(f"couldn't load pretrained model: {e}")
    
    def _get_student_features(self, student: Student) -> torch.Tensor:
        """
        extract features from student model.
        
        Args:
            student: Student model instance
            
        Returns:
            tensor of student features [10]
        """
        # map categorical fields to numbers
        academic_level_map = {'freshman': 1, 'sophomore': 2, 'junior': 3, 'senior': 4, 'graduate': 5}
        study_freq_map = {'rarely': 1, 'monthly': 2, 'biweekly': 3, 'weekly': 4, 'daily': 5}
        
        features = [
            academic_level_map.get(student.academic_level, 3),  # default to junior
            student.gpa / 4.0,  # normalize GPA to 0-1
            student.prior_knowledge_score or 0.5,  # default to 0.5 if none
            study_freq_map.get(student.study_frequency, 3),  # default to biweekly
            student.attendance_rate / 100.0,  # normalize to 0-1
            student.participation_score / 100.0,  # normalize to 0-1
            min(student.total_time_spent.total_seconds() / 3600, 100) / 100 if student.total_time_spent else 0.1,  # hours, cap at 100
            min(student.average_time_per_session.total_seconds() / 3600, 5) / 5 if student.average_time_per_session else 0.2,  # hours, cap at 5
            1.0,  # active student indicator
            0.5   # learning style preference (placeholder for now)
        ]
        
        return torch.tensor(features, dtype=torch.float32)
    
    def _get_mastery_scores(self, student: Student) -> torch.Tensor:
        """
        get current mastery scores for all topics.
        
        Args:
            student: Student model instance
            
        Returns:
            tensor of mastery scores [num_topics]
        """
        mastery_scores = torch.zeros(self.num_topics)
        self.current_observed_topic_indices = set()
        
        # first try to get from KnowledgeState records (if they exist)
        knowledge_states = KnowledgeState.objects.filter(student=student)
        
        if knowledge_states.exists():
            # use ML model predictions if available
            for ks in knowledge_states:
                topic_idx = self.current_topic_to_index.get(ks.topic.name)
                if topic_idx is not None and 0 <= topic_idx < self.num_topics:
                    mastery_scores[topic_idx] = ks.proficiency_score
                    self.current_observed_topic_indices.add(topic_idx)
        else:
            # calculate mastery scores directly from student interactions
            student_state = self.data_prep.get_student_current_state(student.student_id)
            if student_state and 'mastery_scores' in student_state:
                for topic_name, mastery_score in student_state['mastery_scores'].items():
                    topic_idx = self.current_topic_to_index.get(topic_name)
                    if topic_idx is not None and 0 <= topic_idx < self.num_topics:
                        mastery_scores[topic_idx] = mastery_score
                        self.current_observed_topic_indices.add(topic_idx)
        
        return mastery_scores
    
    def _get_weak_topics(self, mastery_scores: torch.Tensor, threshold: float = 0.6) -> List[int]:
        """
        identify weak topics based on mastery scores.
        
        Args:
            mastery_scores: tensor of mastery scores
            threshold: threshold below which topics are considered weak
            
        Returns:
            list of weak topic indices
        """
        weak_indices = []
        for i, score in enumerate(mastery_scores):
            if self.current_observed_topic_indices and i not in self.current_observed_topic_indices:
                continue
            if score < threshold:
                weak_indices.append(i)
        return weak_indices
    
    def _get_prerequisites(self, topic_name: str) -> List[str]:
        """
        get prerequisite topics from knowledge graph.
        
        Args:
            topic_name: name of the topic
            
        Returns:
            list of prerequisite topic names
        """
        prerequisites = []
        
        try:
            # get the knowledge graph
            kg = KnowledgeGraph.objects.filter(is_active=True).first()
            if not kg:
                return prerequisites
            
            # get topic relationships
            relationships = GraphEdge.objects.filter(
                graph=kg,
                target_topic__name=topic_name,
                relationship_type='prerequisite'
            )

            if self.current_course is not None:
                relationships = relationships.filter(
                    target_topic__course=self.current_course,
                    source_topic__course=self.current_course,
                )

            relationships = relationships.select_related('source_topic')
            
            for rel in relationships:
                prerequisites.append(rel.source_topic.name)
                
        except Exception as e:
            logger.warning(f"couldn't get prerequisites for {topic_name}: {e}")
        
        return prerequisites
    
    def _get_related_topics(self, topic_name: str) -> List[str]:
        """
        get related topics from knowledge graph.
        
        Args:
            topic_name: name of the topic
            
        Returns:
            list of related topic names
        """
        related = []
        
        try:
            # get the knowledge graph
            kg = KnowledgeGraph.objects.filter(is_active=True).first()
            if not kg:
                return related
            
            # get topic relationships
            relationships = GraphEdge.objects.filter(
                graph=kg,
                source_topic__name=topic_name,
                relationship_type__in=['related', 'next', 'part_of']
            )

            if self.current_course is not None:
                relationships = relationships.filter(
                    source_topic__course=self.current_course,
                    target_topic__course=self.current_course,
                )

            relationships = relationships.select_related('target_topic')
            
            for rel in relationships:
                related.append(rel.target_topic.name)
                
        except Exception as e:
            logger.warning(f"couldn't get related topics for {topic_name}: {e}")
        
        return related
    
    def _get_topic_resources(self, topic_name: str, difficulty: str = None) -> List[Dict[str, Any]]:
        """
        get learning resources for a topic
        
        Args:
            topic_name: name of the topic
            difficulty: preferred difficulty level
            
        Returns:
            list of resource dictionaries
        """
        try:
            topic = self._resolve_topic(topic_name)
            if not topic:
                logger.warning(f"Topic {topic_name} not found")
                return []
            resources_query = Resource.objects.filter(topics=topic)
            
            # if specific difficulty requested and available, filter by it
            if difficulty:
                difficulty_filtered = resources_query.filter(difficulty=difficulty)
                if difficulty_filtered.exists():
                    resources_query = difficulty_filtered
                # if no resources for that difficulty, use all resources for the topic
            
            resources = []
            for resource in resources_query[:5]:  # limit to 5 resources
                resources.append({
                    'title': resource.title,
                    'description': resource.description,
                    'url': resource.url,
                    'type': resource.resource_type,
                    'difficulty': resource.difficulty,
                    'estimated_time': resource.estimated_time.total_seconds() / 3600 if resource.estimated_time else 1.0
                })
            
            return resources
            
        except Topic.DoesNotExist:
            logger.warning(f"Topic {topic_name} not found")
            return []

    def _resolve_topic(self, topic_name: str) -> Optional[Topic]:
        topics = Topic.objects.filter(name=topic_name)
        if self.current_course is not None:
            topics = topics.filter(course=self.current_course)
        return topics.order_by('id').first()

    def _get_student_course(self, student: Student):
        interaction = student.interactions.select_related(
            'question__assessment__course'
        ).order_by('-timestamp').first()
        if interaction and interaction.question and interaction.question.assessment:
            return interaction.question.assessment.course
        return student.courses.order_by('course_id').first()

    def _set_current_course_context(self, student: Student):
        self.current_course = self._get_student_course(student)
        if self.current_course is None:
            self.current_topics = []
            self.current_topic_to_index = {}
            self.topic_list = []
            self.num_topics = 0
            return

        self.current_topics = list(Topic.objects.filter(course=self.current_course).order_by('id'))
        self.topic_list = [topic.name for topic in self.current_topics]
        self.current_topic_to_index = {
            topic.name: index for index, topic in enumerate(self.current_topics)
        }
        self.num_topics = len(self.current_topics)
    
    def generate_comprehensive_learning_path(self, student_id: str) -> Dict[str, Any]:
        """
        generate a comprehensive learning path with all required information
        
        Args:
            student_id: Student ID
            
        Returns:
            dict containing complete learning path information
        """
        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            logger.error(f"Student {student_id} not found")
            return {}

        self._set_current_course_context(student)
        if self.num_topics == 0:
            return {}
        
        # get student features and mastery scores
        student_features = self._get_student_features(student)
        mastery_scores = self._get_mastery_scores(student)
        student_state = self.data_prep.get_student_current_state(student.student_id)
        total_interactions = student.interactions.count()
        correct_answers = student.interactions.filter(correct=True).count()
        attempted_topics = len(self.current_observed_topic_indices)
        if attempted_topics:
            average_performance = sum(
                mastery_scores[idx].item() for idx in self.current_observed_topic_indices
            ) / attempted_topics
        else:
            average_performance = 0.0
        
        # identify weak topics
        weak_topic_indices = self._get_weak_topics(mastery_scores)
        weak_topics = [
            (i, self.topic_list[i]) for i in weak_topic_indices if i < len(self.topic_list)
        ]
        
        # Use performance-based recommendations scoped to the student's course topics.
        lstm_recommendations = self._generate_mastery_based_recommendations(
            mastery_scores, num_recommendations=min(10, self.num_topics)
        )
        
        # build comprehensive learning path
        learning_path = {
            'student_id': student_id,
            'student_stats': {
                'performance_based': True,
                'path_version': 2,
                'total_interactions': total_interactions,
                'correct_answers': correct_answers,
                'incorrect_answers': max(total_interactions - correct_answers, 0),
                'attempted_topics': attempted_topics,
                'average_performance': average_performance,
                'source': 'smrt_quiz_exercise_performance',
                'recent_activity_count': len(student_state.get('interaction_sequence', [])) if student_state else 0,
            },
            'weak_topics': [],
            'recommended_path': [],
            'total_estimated_time': 0
        }
        
        # process weak topics with prerequisites and resources
        for topic_index, topic_name in weak_topics:
            topic_info = {
                'name': topic_name,
                'current_mastery': mastery_scores[topic_index].item(),
                'prerequisites': self._get_prerequisites(topic_name),
                'related_topics': self._get_related_topics(topic_name),
                'resources': self._get_topic_resources(topic_name)
            }
            learning_path['weak_topics'].append(topic_info)
        
        # process LSTM recommendations
        for rec in lstm_recommendations:
            if rec['topic_id'] < len(self.topic_list):
                topic_name = self.topic_list[rec['topic_id']]
                
                # determine recommended difficulty
                difficulty_probs = rec['difficulty_probs']
                recommended_difficulty = max(difficulty_probs, key=difficulty_probs.get)
                
                # check prerequisites
                prerequisites = self._get_prerequisites(topic_name)
                unmet_prerequisites = []
                for prereq in prerequisites:
                    prereq_idx = self.current_topic_to_index.get(prereq)
                    if prereq_idx is not None and prereq_idx < len(mastery_scores):
                        if mastery_scores[prereq_idx] < 0.7:
                            unmet_prerequisites.append(prereq)
                
                recommendation = {
                    'topic': topic_name,
                    'confidence': rec['confidence'],
                    'recommended_difficulty': recommended_difficulty,
                    'estimated_time_hours': rec['estimated_time_hours'],
                    'prerequisites': prerequisites,
                    'unmet_prerequisites': unmet_prerequisites,
                    'should_study_prerequisites_first': len(unmet_prerequisites) > 0,
                    'related_topics': self._get_related_topics(topic_name),
                    'resources': self._get_topic_resources(topic_name, recommended_difficulty)
                }
                
                learning_path['recommended_path'].append(recommendation)
                learning_path['total_estimated_time'] += rec['estimated_time_hours']
        
        # sort recommendations by confidence and prerequisite requirements
        learning_path['recommended_path'].sort(
            key=lambda x: (len(x['unmet_prerequisites']), -x['confidence'])
        )
        
        return learning_path
    
    def _generate_mastery_based_recommendations(self, mastery_scores: torch.Tensor, 
                                              num_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        generate recommendations based on mastery scores (fallback method)
        
        Args:
            mastery_scores: tensor of mastery scores [num_topics]
            num_recommendations: number of recommendations to generate
            
        Returns:
            list of topic recommendations
        """
        recommendations = []
        
        # create topic recommendations based on mastery scores
        for i, score in enumerate(mastery_scores):
            if i < len(self.topic_list):
                topic_name = self.topic_list[i]
                
                # calculate confidence based on inverse mastery (lower mastery = higher priority)
                # add some randomness to avoid always recommending the same topics
                base_confidence = max(0.1, 1.0 - score.item())
                confidence = base_confidence + np.random.uniform(-0.1, 0.1)
                confidence = max(0.1, min(0.9, confidence))  # clamp between 0.1 and 0.9
                
                recommendations.append({
                    'topic_id': i,
                    'confidence': confidence,
                    'difficulty_probs': {
                        'beginner': 0.7 if score < 0.3 else 0.3,
                        'intermediate': 0.2 if score < 0.3 else 0.5,
                        'advanced': 0.1 if score < 0.3 else 0.2
                    },
                    'estimated_time_hours': 2.0 + (1.0 - score.item()) * 2.0  # 2-4 hours based on mastery
                })
        
        # sort by confidence (highest first) and return top recommendations
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations[:num_recommendations]
