from django.core.management.base import BaseCommand
import logging

from learning_paths.ml.adaptive_lstm_visualizer import AdaptiveLSTMVisualizer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate comprehensive visualizations for Adaptive LSTM model (for research papers)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-size',
            type=int,
            default=50,
            help='Number of students to analyze (default: 50)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='evaluation_results/adaptive_lstm',
            help='Directory to save visualizations'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎨 Starting Adaptive LSTM Visualization Generation...'))
        self.stdout.write('')
        
        sample_size = options['sample_size']
        output_dir = options['output_dir']
        
        self.stdout.write(f'📊 Configuration:')
        self.stdout.write(f'   - Sample Size: {sample_size} students')
        self.stdout.write(f'   - Output Directory: {output_dir}/')
        self.stdout.write('')
        
        # Initialize visualizer
        visualizer = AdaptiveLSTMVisualizer(save_dir=output_dir)
        
        # Generate all visualizations
        self.stdout.write(self.style.SUCCESS('🔍 Analyzing student data and generating recommendations...'))
        
        try:
            visualizer.generate_all_visualizations(sample_size=sample_size)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Visualization generation completed!'))
            self.stdout.write('')
            self.stdout.write('📁 Generated visualizations:')
            self.stdout.write('   1. model_architecture.png - Model architecture diagram')
            self.stdout.write('   2. confidence_distribution.png - Recommendation confidence analysis')
            self.stdout.write('   3. topic_frequency_heatmap.png - Topic recommendation frequencies')
            self.stdout.write('   4. difficulty_distribution.png - Difficulty level distribution')
            self.stdout.write('   5. student_coverage_analysis.png - Student coverage metrics')
            self.stdout.write('   6. prerequisite_satisfaction.png - Prerequisite satisfaction analysis')
            self.stdout.write('   7. time_estimation_analysis.png - Learning time estimates')
            self.stdout.write('   8. mastery_vs_recommendations.png - Mastery correlation analysis')
            self.stdout.write('   9. summary_dashboard.png - Comprehensive summary dashboard')
            self.stdout.write('')
            self.stdout.write(f'📂 All visualizations saved to: {output_dir}/visualizations/')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 Ready for your research paper!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error generating visualizations: {e}'))
            logger.error(f"Visualization generation error: {e}", exc_info=True)
            return
        
        self.stdout.write('')
        self.stdout.write('💡 Tips for your research paper:')
        self.stdout.write('   - Use summary_dashboard.png for an overview')
        self.stdout.write('   - Include model_architecture.png to explain the model')
        self.stdout.write('   - Use confidence_distribution.png to show model reliability')
        self.stdout.write('   - Use topic_frequency_heatmap.png to show recommendation patterns')
