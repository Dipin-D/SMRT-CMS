import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
from pal.core.models import Topic, Course
from pal.knowledge_graph.models import KnowledgeGraph, GraphEdge

class Command(BaseCommand):
    help = 'Load Knowledge Structure Graph from java_ksg.json'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to load Knowledge Structure Graph...'))
        
        # Path to the JSON file
        json_file_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'java_ksg.json')
        
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file_path}'))
            return
        
        with transaction.atomic():
            # Load JSON data
            ksg_data = self.load_json_data(json_file_path)
            if not ksg_data:
                return
            
            # Get or create the CS206 course using only course_id
            course, _ = Course.objects.get_or_create(course_id='CS206')
            
            # Create or update topics from nodes
            topics_created, topics_updated = self.create_or_update_topics(ksg_data['nodes'], course)
            
            # Create or update the knowledge graph
            knowledge_graph = self.create_or_update_knowledge_graph(ksg_data)
            
            # Create graph edges
            edges_created, edges_updated = self.create_graph_edges(ksg_data['edges'], knowledge_graph, course)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded KSG! '
            f'Topics: {topics_created} created, {topics_updated} updated. '
            f'Edges: {edges_created} created, {edges_updated} updated.'
        ))

    def load_json_data(self, json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            self.stdout.write(f'Loaded JSON with {len(data.get("nodes", []))} nodes and {len(data.get("edges", []))} edges')
            return data
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Error parsing JSON file: {e}'))
            return None

    def create_or_update_topics(self, nodes, course):
        topics_created = 0
        topics_updated = 0
        
        for node in nodes:
            topic_name = node.get('name')
            topic_description = node.get('description', '')
            
            if not topic_name:
                continue
            
            topic, created = Topic.objects.get_or_create(
                name=topic_name,
                course=course,
                defaults={'description': topic_description}
            )
            
            if created:
                topics_created += 1
            else:
                if topic.description != topic_description:
                    topic.description = topic_description
                    topic.save()
                    topics_updated += 1
        
        return topics_created, topics_updated

    def create_or_update_knowledge_graph(self, ksg_data):
        default_user, _ = User.objects.get_or_create(
            username='system',
            defaults={'email': 'system@example.com'}
        )
        
        knowledge_graph, created = KnowledgeGraph.objects.get_or_create(
            name=ksg_data.get('name', 'Java Knowledge Structure Graph'),
            version=ksg_data.get('version', '1.0'),
            defaults={
                'description': ksg_data.get('description', ''),
                'created_by': default_user,
                'data': ksg_data,
                'is_active': True
            }
        )
        
        if not created:
            knowledge_graph.description = ksg_data.get('description', '')
            knowledge_graph.data = ksg_data
            knowledge_graph.save()
        
        return knowledge_graph

    def create_graph_edges(self, edges_data, knowledge_graph, course):
        edges_created = 0
        edges_updated = 0
        
        node_id_to_name = {node['id']: node['name'] for node in knowledge_graph.data['nodes']}
        
        for edge in edges_data:
            source_name = node_id_to_name.get(edge.get('from'))
            target_name = node_id_to_name.get(edge.get('to'))
            if not source_name or not target_name:
                continue
            
            try:
                source_topic = Topic.objects.get(name=source_name, course=course)
                target_topic = Topic.objects.get(name=target_name, course=course)
            except Topic.DoesNotExist:
                continue
            
            edge_obj, created = GraphEdge.objects.get_or_create(
                graph=knowledge_graph,
                source_topic=source_topic,
                target_topic=target_topic,
                relationship_type=edge.get('relationship', 'related'),
                defaults={'weight': edge.get('weight', 1.0)}
            )
            
            if created:
                edges_created += 1
            else:
                if edge_obj.weight != edge.get('weight', 1.0):
                    edge_obj.weight = edge.get('weight', 1.0)
                    edge_obj.save()
                    edges_updated += 1
        
        return edges_created, edges_updated