"""
Visualization module for Adaptive Learning Path LSTM model.
Creates research-paper-quality visualizations for model analysis.
"""

import torch
import numpy as np
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.style.use('default')
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    plt = None
    sns = None

from core.models import Student
from learning_paths.ml.adaptive_path_lstm import DjangoIntegratedPathGenerator

logger = logging.getLogger(__name__)


class AdaptiveLSTMVisualizer:
    """
    Generates comprehensive visualizations for the Adaptive LSTM model.
    Designed for research paper presentation.
    """
    
    def __init__(self, save_dir: str = "evaluation_results/adaptive_lstm"):
        """
        Initialize the visualizer.
        
        Args:
            save_dir: Directory to save visualizations
        """
        self.save_dir = save_dir
        self.viz_dir = os.path.join(save_dir, "visualizations")
        os.makedirs(self.viz_dir, exist_ok=True)
        
        # Set up plotting style for publication quality
        if PLOTTING_AVAILABLE:
            plt.style.use('default')
            sns.set_palette("husl")
            plt.rcParams['figure.dpi'] = 300
            plt.rcParams['savefig.dpi'] = 300
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.labelsize'] = 11
            plt.rcParams['axes.titlesize'] = 12
            plt.rcParams['xtick.labelsize'] = 9
            plt.rcParams['ytick.labelsize'] = 9
            plt.rcParams['legend.fontsize'] = 9
        
        self.path_generator = DjangoIntegratedPathGenerator()
    
    def generate_all_visualizations(self, sample_size: int = 50):
        """
        Generate all visualizations for the Adaptive LSTM model.
        
        Args:
            sample_size: Number of students to sample for analysis
        """
        if not PLOTTING_AVAILABLE:
            logger.warning("Matplotlib/seaborn not available. Skipping visualizations.")
            return
        
        logger.info("Generating Adaptive LSTM visualizations...")
        
        # Get student sample
        students = list(Student.objects.all()[:sample_size])
        
        if not students:
            logger.error("No students found in database. Please add student data first.")
            return
        
        logger.info(f"Analyzing {len(students)} students...")
        
        # Collect recommendation data
        recommendation_data = self._collect_recommendation_data(students)
        
        if not recommendation_data['all_recommendations']:
            logger.error("No recommendations generated. Model may need training or data.")
            return
        
        # Generate visualizations
        try:
            # 1. Model Architecture Diagram
            self._plot_model_architecture()
            
            # 2. Recommendation Confidence Distribution
            self._plot_confidence_distribution(recommendation_data)
            
            # 3. Topic Recommendation Frequency Heatmap
            self._plot_topic_frequency_heatmap(recommendation_data)
            
            # 4. Difficulty Level Distribution
            self._plot_difficulty_distribution(recommendation_data)
            
            # 5. Student Coverage Analysis
            self._plot_student_coverage_analysis(recommendation_data)
            
            # 6. Prerequisite Satisfaction Metrics
            self._plot_prerequisite_satisfaction(recommendation_data)
            
            # 7. Time Estimation Analysis
            self._plot_time_estimation_analysis(recommendation_data)
            
            # 8. Topic Mastery vs Recommendations
            self._plot_mastery_vs_recommendations(recommendation_data)
            
            # 9. Comprehensive Summary Dashboard
            self._plot_summary_dashboard(recommendation_data)
            
            logger.info(f"All visualizations saved to {self.viz_dir}")
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
    
    def _collect_recommendation_data(self, students: List[Student]) -> Dict[str, Any]:
        """Collect recommendation data from all students."""
        
        all_recommendations = []
        student_recommendations = {}
        topic_recommendations = defaultdict(int)
        difficulty_recommendations = defaultdict(int)
        confidence_scores = []
        time_estimates = []
        prerequisite_data = []
        mastery_vs_recs = []
        
        for student in students:
            try:
                # Generate learning path
                learning_path = self.path_generator.generate_comprehensive_learning_path(
                    student.student_id
                )
                
                if not learning_path or 'recommended_path' not in learning_path:
                    continue
                
                student_recs = []
                
                for rec in learning_path['recommended_path']:
                    # Collect overall stats
                    topic_recommendations[rec['topic']] += 1
                    confidence_scores.append(rec['confidence'])
                    time_estimates.append(rec['estimated_time_hours'])
                    
                    # Difficulty distribution
                    difficulty_recommendations[rec['recommended_difficulty']] += 1
                    
                    # Prerequisite satisfaction
                    prerequisite_data.append({
                        'topic': rec['topic'],
                        'has_prerequisites': len(rec['prerequisites']) > 0,
                        'unmet_prerequisites': len(rec['unmet_prerequisites']),
                        'total_prerequisites': len(rec['prerequisites']),
                        'satisfaction_rate': 1.0 - (len(rec['unmet_prerequisites']) / max(1, len(rec['prerequisites'])))
                    })
                    
                    student_recs.append(rec)
                    all_recommendations.append(rec)
                
                student_recommendations[student.student_id] = student_recs
                
                # Mastery vs recommendations
                if 'student_stats' in learning_path:
                    mastery_vs_recs.append({
                        'student_id': student.student_id,
                        'average_mastery': learning_path['student_stats']['average_performance'],
                        'num_recommendations': len(student_recs),
                        'avg_confidence': np.mean([r['confidence'] for r in student_recs]) if student_recs else 0
                    })
                
            except Exception as e:
                logger.warning(f"Error processing student {student.student_id}: {e}")
                continue
        
        return {
            'all_recommendations': all_recommendations,
            'student_recommendations': student_recommendations,
            'topic_recommendations': topic_recommendations,
            'difficulty_recommendations': difficulty_recommendations,
            'confidence_scores': confidence_scores,
            'time_estimates': time_estimates,
            'prerequisite_data': prerequisite_data,
            'mastery_vs_recs': mastery_vs_recs
        }
    
    def _plot_model_architecture(self):
        """Create a visual representation of the model architecture."""
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.95, 'Adaptive Learning Path LSTM Architecture', 
                ha='center', va='top', fontsize=14, fontweight='bold')
        
        # Define architecture components with positions
        components = [
            # Input Layer
            {'name': 'Student Profile\n(10 features)', 'pos': (0.15, 0.85), 'color': '#E8F4F8'},
            {'name': 'Topic Mastery\n(N topics)', 'pos': (0.5, 0.85), 'color': '#E8F4F8'},
            {'name': 'Topic Sequence\n(one-hot)', 'pos': (0.85, 0.85), 'color': '#E8F4F8'},
            
            # Encoding Layer
            {'name': 'Student Encoder\n(Linear)', 'pos': (0.15, 0.70), 'color': '#D4E6F1'},
            {'name': 'Mastery Encoder\n(Linear)', 'pos': (0.5, 0.70), 'color': '#D4E6F1'},
            
            # Concatenation
            {'name': 'Feature Concatenation\n(2*hidden + topics)', 'pos': (0.5, 0.55), 'color': '#AED6F1'},
            
            # LSTM Layer
            {'name': 'LSTM Layer\n(2 layers, hidden=128)', 'pos': (0.5, 0.40), 'color': '#85C1E2'},
            
            # Attention Layer
            {'name': 'Multi-Head Attention\n(4 heads)', 'pos': (0.5, 0.25), 'color': '#5DADE2'},
            
            # Output Layers
            {'name': 'Next Topic\nPredictor', 'pos': (0.25, 0.08), 'color': '#FEF5E7'},
            {'name': 'Difficulty\nPredictor', 'pos': (0.5, 0.08), 'color': '#FEF5E7'},
            {'name': 'Time\nEstimator', 'pos': (0.75, 0.08), 'color': '#FEF5E7'},
        ]
        
        # Draw boxes
        for comp in components:
            bbox = dict(boxstyle='round,pad=0.5', facecolor=comp['color'], 
                       edgecolor='black', linewidth=1.5)
            ax.text(comp['pos'][0], comp['pos'][1], comp['name'],
                   ha='center', va='center', bbox=bbox, fontsize=9)
        
        # Draw arrows
        arrows = [
            # Input to encoders
            ((0.15, 0.82), (0.15, 0.73)),
            ((0.5, 0.82), (0.5, 0.73)),
            
            # Encoders to concatenation
            ((0.15, 0.67), (0.35, 0.58)),
            ((0.5, 0.67), (0.5, 0.58)),
            ((0.85, 0.82), (0.65, 0.58)),
            
            # Concatenation to LSTM
            ((0.5, 0.52), (0.5, 0.43)),
            
            # LSTM to Attention
            ((0.5, 0.37), (0.5, 0.28)),
            
            # Attention to outputs
            ((0.5, 0.22), (0.25, 0.12)),
            ((0.5, 0.22), (0.5, 0.12)),
            ((0.5, 0.22), (0.75, 0.12)),
        ]
        
        for start, end in arrows:
            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
        
        # Add legend
        legend_text = (
            "Model Parameters:\n"
            "• Hidden Size: 128\n"
            "• LSTM Layers: 2\n"
            "• Attention Heads: 4\n"
            "• Dropout: 0.3"
        )
        ax.text(0.02, 0.35, legend_text, fontsize=8, 
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'model_architecture.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_confidence_distribution(self, data: Dict[str, Any]):
        """Plot distribution of recommendation confidence scores."""
        
        confidence_scores = data['confidence_scores']
        
        if not confidence_scores:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Overall distribution
        ax1.hist(confidence_scores, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(confidence_scores), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(confidence_scores):.3f}')
        ax1.axvline(np.median(confidence_scores), color='green', linestyle='--', 
                   linewidth=2, label=f'Median: {np.median(confidence_scores):.3f}')
        ax1.set_xlabel('Confidence Score')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Overall Confidence Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(confidence_scores, vert=True)
        ax2.set_ylabel('Confidence Score')
        ax2.set_title('Confidence Score Statistics')
        ax2.grid(True, alpha=0.3)
        
        # Cumulative distribution
        sorted_scores = np.sort(confidence_scores)
        cumulative = np.arange(1, len(sorted_scores) + 1) / len(sorted_scores)
        ax3.plot(sorted_scores, cumulative, linewidth=2, color='purple')
        ax3.set_xlabel('Confidence Score')
        ax3.set_ylabel('Cumulative Probability')
        ax3.set_title('Cumulative Distribution Function')
        ax3.grid(True, alpha=0.3)
        
        # Statistics table
        ax4.axis('off')
        stats_data = [
            ['Metric', 'Value'],
            ['Mean', f'{np.mean(confidence_scores):.4f}'],
            ['Median', f'{np.median(confidence_scores):.4f}'],
            ['Std Dev', f'{np.std(confidence_scores):.4f}'],
            ['Min', f'{np.min(confidence_scores):.4f}'],
            ['Max', f'{np.max(confidence_scores):.4f}'],
            ['Q1', f'{np.percentile(confidence_scores, 25):.4f}'],
            ['Q3', f'{np.percentile(confidence_scores, 75):.4f}'],
            ['Total Recs', f'{len(confidence_scores)}']
        ]
        
        table = ax4.table(cellText=stats_data, cellLoc='left', loc='center',
                         colWidths=[0.4, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header row
        for i in range(2):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.suptitle('Recommendation Confidence Analysis', fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'confidence_distribution.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_topic_frequency_heatmap(self, data: Dict[str, Any]):
        """Plot heatmap of topic recommendation frequencies."""
        
        topic_recs = data['topic_recommendations']
        
        if not topic_recs:
            return
        
        # Sort topics by frequency
        sorted_topics = sorted(topic_recs.items(), key=lambda x: x[1], reverse=True)
        topics = [t[0] for t in sorted_topics[:20]]  # Top 20 topics
        frequencies = [t[1] for t in sorted_topics[:20]]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart
        bars = ax1.barh(range(len(topics)), frequencies, color='steelblue')
        ax1.set_yticks(range(len(topics)))
        ax1.set_yticklabels(topics, fontsize=8)
        ax1.set_xlabel('Number of Recommendations')
        ax1.set_title('Top 20 Most Recommended Topics')
        ax1.invert_yaxis()
        
        # Add value labels
        for i, (bar, freq) in enumerate(zip(bars, frequencies)):
            ax1.text(freq + max(frequencies) * 0.01, i, str(freq), 
                    va='center', fontsize=8)
        
        # Create a grid heatmap showing recommendation patterns
        # Group topics and show frequency matrix
        topic_names = list(topic_recs.keys())[:15]  # Limit to 15 for readability
        freq_matrix = np.array([[topic_recs[t]] for t in topic_names])
        
        im = ax2.imshow(freq_matrix, cmap='YlOrRd', aspect='auto')
        ax2.set_yticks(range(len(topic_names)))
        ax2.set_yticklabels(topic_names, fontsize=8)
        ax2.set_xticks([0])
        ax2.set_xticklabels(['Frequency'])
        ax2.set_title('Topic Recommendation Heatmap')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label('Number of Recommendations', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(topic_names)):
            text = ax2.text(0, i, str(int(freq_matrix[i, 0])),
                          ha="center", va="center", color="black", fontsize=8)
        
        plt.suptitle('Topic Recommendation Frequency Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'topic_frequency_heatmap.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_difficulty_distribution(self, data: Dict[str, Any]):
        """Plot distribution of recommended difficulty levels."""
        
        difficulty_dist = data['difficulty_recommendations']
        
        if not difficulty_dist:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Pie chart
        difficulties = list(difficulty_dist.keys())
        counts = list(difficulty_dist.values())
        colors = ['#90EE90', '#FFD700', '#FF6347']  # Green, Gold, Red
        
        wedges, texts, autotexts = ax1.pie(counts, labels=difficulties, autopct='%1.1f%%',
                                            colors=colors, startangle=90)
        ax1.set_title('Difficulty Level Distribution')
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        # Bar chart
        bars = ax2.bar(difficulties, counts, color=colors, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Number of Recommendations')
        ax2.set_title('Difficulty Level Counts')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{count}\n({count/sum(counts)*100:.1f}%)',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.suptitle('Recommended Difficulty Level Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'difficulty_distribution.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_student_coverage_analysis(self, data: Dict[str, Any]):
        """Analyze how recommendations are distributed across students."""
        
        student_recs = data['student_recommendations']
        
        if not student_recs:
            return
        
        # Calculate stats per student
        recs_per_student = [len(recs) for recs in student_recs.values()]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Distribution of recommendations per student
        ax1.hist(recs_per_student, bins=15, alpha=0.7, color='coral', edgecolor='black')
        ax1.axvline(np.mean(recs_per_student), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(recs_per_student):.1f}')
        ax1.set_xlabel('Number of Recommendations')
        ax1.set_ylabel('Number of Students')
        ax1.set_title('Recommendations per Student Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot of recommendations per student
        ax2.boxplot(recs_per_student, vert=True)
        ax2.set_ylabel('Number of Recommendations')
        ax2.set_title('Recommendations per Student Statistics')
        ax2.grid(True, alpha=0.3)
        
        # Student coverage (students with at least N recommendations)
        thresholds = range(1, max(recs_per_student) + 1)
        coverage = [sum(1 for x in recs_per_student if x >= t) for t in thresholds]
        coverage_pct = [c / len(student_recs) * 100 for c in coverage]
        
        ax3.plot(thresholds, coverage_pct, marker='o', linewidth=2, markersize=6, color='purple')
        ax3.set_xlabel('Minimum Number of Recommendations')
        ax3.set_ylabel('% of Students')
        ax3.set_title('Student Coverage by Recommendation Threshold')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([0, 105])
        
        # Statistics table
        ax4.axis('off')
        stats_data = [
            ['Metric', 'Value'],
            ['Total Students', f'{len(student_recs)}'],
            ['Avg Recs/Student', f'{np.mean(recs_per_student):.2f}'],
            ['Median Recs/Student', f'{np.median(recs_per_student):.2f}'],
            ['Min Recs', f'{np.min(recs_per_student)}'],
            ['Max Recs', f'{np.max(recs_per_student)}'],
            ['Std Dev', f'{np.std(recs_per_student):.2f}'],
            ['Total Recs', f'{sum(recs_per_student)}'],
        ]
        
        table = ax4.table(cellText=stats_data, cellLoc='left', loc='center',
                         colWidths=[0.5, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header
        for i in range(2):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.suptitle('Student Coverage Analysis', fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'student_coverage_analysis.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_prerequisite_satisfaction(self, data: Dict[str, Any]):
        """Analyze prerequisite satisfaction in recommendations."""
        
        prereq_data = data['prerequisite_data']
        
        if not prereq_data:
            return
        
        # Calculate statistics
        topics_with_prereqs = sum(1 for p in prereq_data if p['has_prerequisites'])
        satisfaction_rates = [p['satisfaction_rate'] for p in prereq_data if p['has_prerequisites']]
        unmet_counts = [p['unmet_prerequisites'] for p in prereq_data if p['has_prerequisites']]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Prerequisite satisfaction rate distribution
        if satisfaction_rates:
            ax1.hist(satisfaction_rates, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            ax1.axvline(np.mean(satisfaction_rates), color='red', linestyle='--', 
                       linewidth=2, label=f'Mean: {np.mean(satisfaction_rates):.2f}')
            ax1.set_xlabel('Prerequisite Satisfaction Rate')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Prerequisite Satisfaction Distribution')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # Pie chart: topics with/without prerequisites
        prereq_counts = [
            topics_with_prereqs,
            len(prereq_data) - topics_with_prereqs
        ]
        ax2.pie(prereq_counts, labels=['With Prerequisites', 'No Prerequisites'],
               autopct='%1.1f%%', colors=['#FF9999', '#66B2FF'], startangle=90)
        ax2.set_title('Topics with Prerequisites')
        
        # Unmet prerequisites distribution
        if unmet_counts:
            unmet_counter = Counter(unmet_counts)
            counts = sorted(unmet_counter.items())
            x_vals = [c[0] for c in counts]
            y_vals = [c[1] for c in counts]
            
            bars = ax3.bar(x_vals, y_vals, color='salmon', edgecolor='black')
            ax3.set_xlabel('Number of Unmet Prerequisites')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Unmet Prerequisites Distribution')
            ax3.grid(True, alpha=0.3, axis='y')
            
            # Add value labels
            for bar, val in zip(bars, y_vals):
                ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        str(val), ha='center', va='bottom', fontsize=9)
        
        # Statistics table
        ax4.axis('off')
        
        if satisfaction_rates:
            stats_data = [
                ['Metric', 'Value'],
                ['Total Recommendations', f'{len(prereq_data)}'],
                ['With Prerequisites', f'{topics_with_prereqs}'],
                ['Without Prerequisites', f'{len(prereq_data) - topics_with_prereqs}'],
                ['Avg Satisfaction Rate', f'{np.mean(satisfaction_rates):.2%}'],
                ['Median Satisfaction', f'{np.median(satisfaction_rates):.2%}'],
                ['Perfect Satisfaction', f'{sum(1 for x in satisfaction_rates if x == 1.0)}'],
                ['Avg Unmet Prereqs', f'{np.mean(unmet_counts):.2f}'],
            ]
        else:
            stats_data = [
                ['Metric', 'Value'],
                ['Total Recommendations', f'{len(prereq_data)}'],
                ['With Prerequisites', '0'],
                ['Without Prerequisites', f'{len(prereq_data)}'],
            ]
        
        table = ax4.table(cellText=stats_data, cellLoc='left', loc='center',
                         colWidths=[0.5, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header
        for i in range(2):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.suptitle('Prerequisite Satisfaction Analysis', fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'prerequisite_satisfaction.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_time_estimation_analysis(self, data: Dict[str, Any]):
        """Analyze time estimation for recommendations."""
        
        time_estimates = data['time_estimates']
        
        if not time_estimates:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Distribution
        ax1.hist(time_estimates, bins=25, alpha=0.7, color='lightblue', edgecolor='black')
        ax1.axvline(np.mean(time_estimates), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(time_estimates):.2f}h')
        ax1.set_xlabel('Estimated Time (hours)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Time Estimation Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(time_estimates, vert=True)
        ax2.set_ylabel('Estimated Time (hours)')
        ax2.set_title('Time Estimation Statistics')
        ax2.grid(True, alpha=0.3)
        
        # Cumulative time
        sorted_times = np.sort(time_estimates)
        cumulative_time = np.cumsum(sorted_times)
        
        ax3.plot(range(len(cumulative_time)), cumulative_time, linewidth=2, color='green')
        ax3.set_xlabel('Number of Recommendations')
        ax3.set_ylabel('Cumulative Time (hours)')
        ax3.set_title('Cumulative Learning Time')
        ax3.grid(True, alpha=0.3)
        
        # Time categories
        time_ranges = ['0-1h', '1-2h', '2-3h', '3-4h', '4+h']
        range_counts = [
            sum(1 for t in time_estimates if t < 1),
            sum(1 for t in time_estimates if 1 <= t < 2),
            sum(1 for t in time_estimates if 2 <= t < 3),
            sum(1 for t in time_estimates if 3 <= t < 4),
            sum(1 for t in time_estimates if t >= 4)
        ]
        
        bars = ax4.bar(time_ranges, range_counts, color='orange', edgecolor='black')
        ax4.set_ylabel('Number of Recommendations')
        ax4.set_title('Time Estimate Categories')
        ax4.grid(True, alpha=0.3, axis='y')
        
        for bar, count in zip(bars, range_counts):
            if count > 0:
                ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        str(count), ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('Learning Time Estimation Analysis', fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'time_estimation_analysis.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_mastery_vs_recommendations(self, data: Dict[str, Any]):
        """Plot relationship between student mastery and recommendations."""
        
        mastery_data = data['mastery_vs_recs']
        
        if not mastery_data:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Scatter: Mastery vs Number of Recommendations
        masteries = [d['average_mastery'] for d in mastery_data]
        num_recs = [d['num_recommendations'] for d in mastery_data]
        
        ax1.scatter(masteries, num_recs, alpha=0.6, s=100, color='purple')
        ax1.set_xlabel('Average Mastery Score')
        ax1.set_ylabel('Number of Recommendations')
        ax1.set_title('Mastery vs Recommendation Count')
        ax1.grid(True, alpha=0.3)
        
        # Add trend line
        if len(masteries) > 1:
            z = np.polyfit(masteries, num_recs, 1)
            p = np.poly1d(z)
            ax1.plot(sorted(masteries), p(sorted(masteries)), "r--", alpha=0.8, linewidth=2)
        
        # Scatter: Mastery vs Average Confidence
        avg_confidences = [d['avg_confidence'] for d in mastery_data]
        
        ax2.scatter(masteries, avg_confidences, alpha=0.6, s=100, color='green')
        ax2.set_xlabel('Average Mastery Score')
        ax2.set_ylabel('Average Recommendation Confidence')
        ax2.set_title('Mastery vs Recommendation Confidence')
        ax2.grid(True, alpha=0.3)
        
        # Add trend line
        if len(masteries) > 1:
            z = np.polyfit(masteries, avg_confidences, 1)
            p = np.poly1d(z)
            ax2.plot(sorted(masteries), p(sorted(masteries)), "r--", alpha=0.8, linewidth=2)
        
        # Mastery distribution
        ax3.hist(masteries, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.axvline(np.mean(masteries), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(masteries):.3f}')
        ax3.set_xlabel('Average Mastery Score')
        ax3.set_ylabel('Number of Students')
        ax3.set_title('Student Mastery Distribution')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Statistics table
        ax4.axis('off')
        stats_data = [
            ['Metric', 'Value'],
            ['Avg Mastery', f'{np.mean(masteries):.4f}'],
            ['Std Dev Mastery', f'{np.std(masteries):.4f}'],
            ['Avg Recs/Student', f'{np.mean(num_recs):.2f}'],
            ['Correlation (M vs R)', f'{np.corrcoef(masteries, num_recs)[0,1]:.3f}'],
            ['Correlation (M vs C)', f'{np.corrcoef(masteries, avg_confidences)[0,1]:.3f}'],
        ]
        
        table = ax4.table(cellText=stats_data, cellLoc='left', loc='center',
                         colWidths=[0.5, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        for i in range(2):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.suptitle('Mastery vs Recommendations Analysis', fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(os.path.join(self.viz_dir, 'mastery_vs_recommendations.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_summary_dashboard(self, data: Dict[str, Any]):
        """Create a comprehensive summary dashboard."""
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Title
        fig.suptitle('Adaptive LSTM Model - Comprehensive Summary Dashboard', 
                    fontsize=16, fontweight='bold')
        
        # 1. Key metrics
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.axis('off')
        
        metrics_text = f"""KEY METRICS
        
Total Recommendations: {len(data['all_recommendations'])}
Total Students: {len(data['student_recommendations'])}
Unique Topics: {len(data['topic_recommendations'])}

Avg Confidence: {np.mean(data['confidence_scores']):.3f}
Avg Time/Rec: {np.mean(data['time_estimates']):.2f}h
Total Est. Time: {sum(data['time_estimates']):.1f}h
"""
        ax1.text(0.1, 0.5, metrics_text, transform=ax1.transAxes, 
                fontsize=10, verticalalignment='center', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 2. Confidence distribution (small)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(data['confidence_scores'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.set_title('Confidence Distribution', fontsize=10)
        ax2.set_xlabel('Confidence', fontsize=9)
        ax2.set_ylabel('Frequency', fontsize=9)
        ax2.tick_params(labelsize=8)
        
        # 3. Difficulty distribution
        ax3 = fig.add_subplot(gs[0, 2])
        difficulties = list(data['difficulty_recommendations'].keys())
        counts = list(data['difficulty_recommendations'].values())
        ax3.pie(counts, labels=difficulties, autopct='%1.1f%%', startangle=90)
        ax3.set_title('Difficulty Distribution', fontsize=10)
        
        # 4. Top topics
        ax4 = fig.add_subplot(gs[1, :])
        sorted_topics = sorted(data['topic_recommendations'].items(), key=lambda x: x[1], reverse=True)
        top_topics = [t[0] for t in sorted_topics[:10]]
        top_freqs = [t[1] for t in sorted_topics[:10]]
        
        bars = ax4.barh(range(len(top_topics)), top_freqs, color='steelblue')
        ax4.set_yticks(range(len(top_topics)))
        ax4.set_yticklabels(top_topics, fontsize=9)
        ax4.set_xlabel('Number of Recommendations', fontsize=10)
        ax4.set_title('Top 10 Most Recommended Topics', fontsize=11)
        ax4.invert_yaxis()
        
        for i, (bar, freq) in enumerate(zip(bars, top_freqs)):
            ax4.text(freq + max(top_freqs) * 0.01, i, str(freq), 
                    va='center', fontsize=8)
        
        # 5. Student coverage
        ax5 = fig.add_subplot(gs[2, 0])
        recs_per_student = [len(recs) for recs in data['student_recommendations'].values()]
        ax5.hist(recs_per_student, bins=15, alpha=0.7, color='coral', edgecolor='black')
        ax5.set_xlabel('Recs per Student', fontsize=9)
        ax5.set_ylabel('# Students', fontsize=9)
        ax5.set_title('Student Coverage', fontsize=10)
        ax5.tick_params(labelsize=8)
        
        # 6. Time estimation
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.hist(data['time_estimates'], bins=20, alpha=0.7, color='lightblue', edgecolor='black')
        ax6.set_xlabel('Estimated Time (h)', fontsize=9)
        ax6.set_ylabel('Frequency', fontsize=9)
        ax6.set_title('Time Estimation', fontsize=10)
        ax6.tick_params(labelsize=8)
        
        # 7. Prerequisite satisfaction
        ax7 = fig.add_subplot(gs[2, 2])
        prereq_data = data['prerequisite_data']
        topics_with_prereqs = sum(1 for p in prereq_data if p['has_prerequisites'])
        prereq_counts = [topics_with_prereqs, len(prereq_data) - topics_with_prereqs]
        
        ax7.pie(prereq_counts, labels=['With Prereqs', 'No Prereqs'],
               autopct='%1.1f%%', colors=['#FF9999', '#66B2FF'], startangle=90)
        ax7.set_title('Prerequisite Coverage', fontsize=10)
        
        plt.savefig(os.path.join(self.viz_dir, 'summary_dashboard.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
