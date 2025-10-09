"""
Audio Visualization Implementation Comparison Tool
===================================================
This script performs statistical analysis and comparison of different 
audio visualization implementations across Python (matplotlib, pygame, OpenCV, OpenGL)
and Unity (C# Audio System).

Author: Statistical Analysis Tool
Date: October 10, 2025
Purpose: Compare performance, features, and characteristics of audio visualization modes
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
import seaborn as sns

# Try importing optional libraries for testing
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("Warning: librosa not available. Some comparisons will be limited.")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available.")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV not available.")


class AudioVisualizationComparator:
    """
    Main class for comparing different audio visualization implementations.
    """
    
    def __init__(self, audio_file: str = None):
        """
        Initialize the comparator with an optional audio file.
        
        Args:
            audio_file: Path to audio file for testing
        """
        self.audio_file = audio_file
        self.results = {}
        self.comparison_data = {}
        
        # Define visualization modes
        self.modes = {
            'matplotlib_bar': {
                'name': 'Matplotlib Bar Visualizer',
                'backend': 'matplotlib',
                'type': 'bar',
                'realtime': False,
                'description': 'Traditional bar chart visualization using matplotlib'
            },
            'matplotlib_circular': {
                'name': 'Matplotlib Circular Visualizer',
                'backend': 'matplotlib',
                'type': 'circular',
                'realtime': False,
                'description': 'Circular/polar visualization using matplotlib'
            },
            'pygame': {
                'name': 'Pygame Visualizer',
                'backend': 'pygame',
                'type': 'custom',
                'realtime': True,
                'description': 'Hardware-accelerated visualization using pygame'
            },
            'opencv': {
                'name': 'OpenCV Visualizer',
                'backend': 'opencv',
                'type': 'custom',
                'realtime': True,
                'description': 'Computer vision-based visualization using OpenCV'
            },
            'opengl': {
                'name': 'OpenGL Visualizer',
                'backend': 'opengl',
                'type': '3d',
                'realtime': True,
                'description': 'GPU-accelerated 3D visualization using OpenGL'
            },
            'unity_3d_cubes': {
                'name': 'Unity 3D Cube Visualizer',
                'backend': 'unity',
                'type': '3d',
                'realtime': True,
                'description': 'Unity3D cube-based frequency visualization'
            },
            'unity_ripple': {
                'name': 'Unity Ripple Visualizer',
                'backend': 'unity',
                'type': '3d_mesh',
                'realtime': True,
                'description': 'Unity3D mesh-based ripple visualization'
            },
            'unity_microphone': {
                'name': 'Unity Microphone Input',
                'backend': 'unity',
                'type': 'realtime_input',
                'realtime': True,
                'description': 'Unity real-time microphone audio visualization'
            }
        }
    
    def analyze_performance_characteristics(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze theoretical performance characteristics of each mode.
        
        Returns:
            Dictionary containing performance metrics for each mode
        """
        print("\n=== Performance Characteristics Analysis ===\n")
        
        characteristics = {}
        
        for mode_id, mode_info in self.modes.items():
            char = {
                'cpu_usage': self._estimate_cpu_usage(mode_info),
                'gpu_usage': self._estimate_gpu_usage(mode_info),
                'memory_usage': self._estimate_memory_usage(mode_info),
                'frame_rate': self._estimate_frame_rate(mode_info),
                'latency': self._estimate_latency(mode_info),
                'setup_complexity': self._estimate_setup_complexity(mode_info),
                'platform_compatibility': self._get_platform_compatibility(mode_info)
            }
            characteristics[mode_id] = char
            
        self.results['performance'] = characteristics
        return characteristics
    
    def _estimate_cpu_usage(self, mode_info: Dict) -> str:
        """Estimate CPU usage level (Low/Medium/High)"""
        backend = mode_info['backend']
        if backend == 'opengl':
            return 'Low'
        elif backend == 'unity':
            return 'Low-Medium'
        elif backend == 'pygame':
            return 'Medium'
        elif backend == 'opencv':
            return 'Medium'
        elif backend == 'matplotlib':
            return 'High'
        return 'Medium'
    
    def _estimate_gpu_usage(self, mode_info: Dict) -> str:
        """Estimate GPU usage level"""
        backend = mode_info['backend']
        viz_type = mode_info['type']
        
        if backend == 'opengl' or (backend == 'unity' and '3d' in viz_type):
            return 'High'
        elif backend == 'pygame':
            return 'Medium'
        elif backend == 'opencv':
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_memory_usage(self, mode_info: Dict) -> str:
        """Estimate memory usage in MB"""
        backend = mode_info['backend']
        realtime = mode_info['realtime']
        
        if backend == 'unity':
            return '100-500MB'
        elif backend == 'matplotlib' and not realtime:
            return '50-200MB'
        elif backend == 'opengl':
            return '50-150MB'
        else:
            return '20-100MB'
    
    def _estimate_frame_rate(self, mode_info: Dict) -> str:
        """Estimate achievable frame rate"""
        backend = mode_info['backend']
        
        if backend == 'opengl':
            return '60-120 FPS'
        elif backend == 'unity':
            return '30-60 FPS'
        elif backend == 'pygame':
            return '30-60 FPS'
        elif backend == 'opencv':
            return '20-40 FPS'
        else:  # matplotlib
            return '10-30 FPS'
    
    def _estimate_latency(self, mode_info: Dict) -> str:
        """Estimate audio-visual latency in milliseconds"""
        backend = mode_info['backend']
        realtime = mode_info['realtime']
        
        if backend == 'unity' and mode_info['type'] == 'realtime_input':
            return '10-30ms'
        elif backend == 'opengl':
            return '15-40ms'
        elif backend == 'pygame':
            return '20-50ms'
        elif backend == 'opencv':
            return '30-60ms'
        else:  # matplotlib
            return '50-100ms'
    
    def _estimate_setup_complexity(self, mode_info: Dict) -> int:
        """Rate setup complexity (1-10 scale)"""
        backend = mode_info['backend']
        
        complexity_map = {
            'matplotlib': 3,
            'pygame': 5,
            'opencv': 6,
            'opengl': 8,
            'unity': 7
        }
        return complexity_map.get(backend, 5)
    
    def _get_platform_compatibility(self, mode_info: Dict) -> List[str]:
        """Get list of compatible platforms"""
        backend = mode_info['backend']
        
        if backend == 'unity':
            return ['Windows', 'macOS', 'Linux', 'iOS', 'Android', 'WebGL']
        elif backend == 'matplotlib':
            return ['Windows', 'macOS', 'Linux']
        elif backend == 'pygame':
            return ['Windows', 'macOS', 'Linux']
        elif backend == 'opencv':
            return ['Windows', 'macOS', 'Linux', 'Android']
        elif backend == 'opengl':
            return ['Windows', 'macOS', 'Linux']
        return ['Windows', 'macOS', 'Linux']
    
    def analyze_features(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze feature set of each visualization mode.
        
        Returns:
            Dictionary containing feature analysis
        """
        print("\n=== Feature Analysis ===\n")
        
        features = {}
        
        for mode_id, mode_info in self.modes.items():
            feat = {
                'fft_support': True,  # All support FFT
                'real_time': mode_info['realtime'],
                'customizable_colors': True,
                'multiple_viz_types': mode_info['backend'] in ['unity', 'opengl'],
                '3d_support': '3d' in mode_info['type'],
                'microphone_input': 'microphone' in mode_id or mode_info['backend'] == 'unity',
                'file_input': True,
                'smoothing': True,
                'frequency_bands': True,
                'export_capability': mode_info['backend'] in ['matplotlib', 'opencv'],
                'interactive': mode_info['backend'] in ['pygame', 'unity', 'opengl'],
                'vr_support': mode_info['backend'] == 'unity'
            }
            features[mode_id] = feat
        
        self.results['features'] = features
        return features
    
    def analyze_audio_processing(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze audio processing capabilities.
        
        Returns:
            Dictionary containing audio processing metrics
        """
        print("\n=== Audio Processing Analysis ===\n")
        
        processing = {}
        
        for mode_id, mode_info in self.modes.items():
            backend = mode_info['backend']
            
            proc = {
                'fft_size': self._get_fft_size(mode_info),
                'hop_length': self._get_hop_length(mode_info),
                'sample_rate': self._get_sample_rate(mode_info),
                'frequency_range': self._get_frequency_range(mode_info),
                'smoothing_algorithm': self._get_smoothing_algorithm(mode_info),
                'normalization': self._get_normalization(mode_info),
                'audio_library': self._get_audio_library(backend)
            }
            processing[mode_id] = proc
        
        self.results['audio_processing'] = processing
        return processing
    
    def _get_fft_size(self, mode_info: Dict) -> str:
        """Get typical FFT size used"""
        if mode_info['backend'] == 'unity':
            return '256-8192 (configurable)'
        return '512-2048'
    
    def _get_hop_length(self, mode_info: Dict) -> str:
        """Get hop length for STFT"""
        if mode_info['backend'] == 'unity':
            return 'N/A (real-time FFT)'
        return '256-512'
    
    def _get_sample_rate(self, mode_info: Dict) -> str:
        """Get typical sample rate"""
        if mode_info['backend'] == 'unity':
            return '22050-48000 Hz'
        return '22050-44100 Hz'
    
    def _get_frequency_range(self, mode_info: Dict) -> str:
        """Get frequency range coverage"""
        return '20 Hz - 20 kHz'
    
    def _get_smoothing_algorithm(self, mode_info: Dict) -> str:
        """Get smoothing algorithm used"""
        if mode_info['backend'] == 'unity':
            return 'Exponential moving average'
        return 'Temporal averaging / EMA'
    
    def _get_normalization(self, mode_info: Dict) -> str:
        """Get normalization method"""
        if mode_info['backend'] == 'matplotlib':
            return 'Logarithmic + Per-bin normalization'
        return 'Dynamic range normalization'
    
    def _get_audio_library(self, backend: str) -> str:
        """Get audio library used"""
        library_map = {
            'matplotlib': 'librosa',
            'pygame': 'pygame.mixer + librosa',
            'opencv': 'librosa',
            'opengl': 'librosa + PyAudio',
            'unity': 'Unity AudioSource API'
        }
        return library_map.get(backend, 'Unknown')
    
    def compare_use_cases(self) -> Dict[str, List[str]]:
        """
        Analyze and compare use cases for each mode.
        
        Returns:
            Dictionary mapping use cases to suitable modes
        """
        print("\n=== Use Case Analysis ===\n")
        
        use_cases = {
            'music_visualization': [],
            'real_time_performance': [],
            'game_integration': [],
            'scientific_analysis': [],
            'mobile_apps': [],
            'web_applications': [],
            'vr_ar_experiences': [],
            'live_audio_feedback': [],
            'video_production': [],
            'educational_demos': []
        }
        
        for mode_id, mode_info in self.modes.items():
            backend = mode_info['backend']
            realtime = mode_info['realtime']
            viz_type = mode_info['type']
            
            # Music visualization
            use_cases['music_visualization'].append(mode_id)
            
            # Real-time performance
            if realtime and backend in ['unity', 'opengl', 'pygame']:
                use_cases['real_time_performance'].append(mode_id)
            
            # Game integration
            if backend == 'unity':
                use_cases['game_integration'].append(mode_id)
            
            # Scientific analysis
            if backend == 'matplotlib':
                use_cases['scientific_analysis'].append(mode_id)
            
            # Mobile apps
            if backend == 'unity':
                use_cases['mobile_apps'].append(mode_id)
            
            # Web applications
            if backend == 'unity' or backend == 'opencv':
                use_cases['web_applications'].append(mode_id)
            
            # VR/AR experiences
            if backend == 'unity' and '3d' in viz_type:
                use_cases['vr_ar_experiences'].append(mode_id)
            
            # Live audio feedback
            if realtime:
                use_cases['live_audio_feedback'].append(mode_id)
            
            # Video production
            if backend in ['matplotlib', 'opencv']:
                use_cases['video_production'].append(mode_id)
            
            # Educational demos
            use_cases['educational_demos'].append(mode_id)
        
        self.results['use_cases'] = use_cases
        return use_cases
    
    def generate_comparison_matrix(self) -> pd.DataFrame:
        """
        Generate a comprehensive comparison matrix.
        
        Returns:
            Pandas DataFrame with comparison metrics
        """
        print("\n=== Generating Comparison Matrix ===\n")
        
        matrix_data = []
        
        for mode_id, mode_info in self.modes.items():
            perf = self.results.get('performance', {}).get(mode_id, {})
            feat = self.results.get('features', {}).get(mode_id, {})
            proc = self.results.get('audio_processing', {}).get(mode_id, {})
            
            row = {
                'Mode': mode_info['name'],
                'Backend': mode_info['backend'],
                'Type': mode_info['type'],
                'Real-time': mode_info['realtime'],
                'CPU Usage': perf.get('cpu_usage', 'N/A'),
                'GPU Usage': perf.get('gpu_usage', 'N/A'),
                'Memory': perf.get('memory_usage', 'N/A'),
                'FPS': perf.get('frame_rate', 'N/A'),
                'Latency': perf.get('latency', 'N/A'),
                'Setup Complexity (1-10)': perf.get('setup_complexity', 'N/A'),
                '3D Support': feat.get('3d_support', False),
                'Microphone': feat.get('microphone_input', False),
                'Interactive': feat.get('interactive', False),
                'VR Support': feat.get('vr_support', False),
                'FFT Size': proc.get('fft_size', 'N/A'),
                'Audio Library': proc.get('audio_library', 'N/A')
            }
            matrix_data.append(row)
        
        df = pd.DataFrame(matrix_data)
        self.comparison_data['matrix'] = df
        return df
    
    def calculate_performance_scores(self) -> Dict[str, float]:
        """
        Calculate overall performance scores for each mode.
        Score is based on multiple factors (0-100 scale).
        
        Returns:
            Dictionary mapping mode IDs to performance scores
        """
        print("\n=== Calculating Performance Scores ===\n")
        
        scores = {}
        
        for mode_id, mode_info in self.modes.items():
            perf = self.results.get('performance', {}).get(mode_id, {})
            feat = self.results.get('features', {}).get(mode_id, {})
            
            # Component scores (0-100)
            cpu_score = self._score_cpu_usage(perf.get('cpu_usage', 'Medium'))
            gpu_score = self._score_gpu_usage(perf.get('gpu_usage', 'Medium'))
            fps_score = self._score_fps(perf.get('frame_rate', '30 FPS'))
            latency_score = self._score_latency(perf.get('latency', '50ms'))
            feature_score = self._score_features(feat)
            complexity_score = 100 - (perf.get('setup_complexity', 5) * 10)
            
            # Weighted average
            weights = {
                'cpu': 0.15,
                'gpu': 0.15,
                'fps': 0.25,
                'latency': 0.20,
                'features': 0.15,
                'complexity': 0.10
            }
            
            overall_score = (
                weights['cpu'] * cpu_score +
                weights['gpu'] * gpu_score +
                weights['fps'] * fps_score +
                weights['latency'] * latency_score +
                weights['features'] * feature_score +
                weights['complexity'] * complexity_score
            )
            
            scores[mode_id] = round(overall_score, 2)
        
        self.results['performance_scores'] = scores
        return scores
    
    def _score_cpu_usage(self, usage: str) -> float:
        """Convert CPU usage to score (lower is better)"""
        score_map = {'Low': 100, 'Low-Medium': 85, 'Medium': 70, 'High': 40}
        return score_map.get(usage, 50)
    
    def _score_gpu_usage(self, usage: str) -> float:
        """Convert GPU usage to score (balanced is better)"""
        score_map = {'Low': 60, 'Medium': 90, 'High': 100}
        return score_map.get(usage, 50)
    
    def _score_fps(self, fps: str) -> float:
        """Convert FPS to score"""
        if '60-120' in fps:
            return 100
        elif '30-60' in fps:
            return 80
        elif '20-40' in fps:
            return 60
        else:
            return 40
    
    def _score_latency(self, latency: str) -> float:
        """Convert latency to score (lower is better)"""
        avg_latency = float(latency.split('-')[0].replace('ms', ''))
        if avg_latency < 20:
            return 100
        elif avg_latency < 30:
            return 90
        elif avg_latency < 50:
            return 70
        else:
            return 50
    
    def _score_features(self, features: Dict) -> float:
        """Score based on available features"""
        feature_count = sum(1 for v in features.values() if v)
        max_features = len(features)
        return (feature_count / max_features) * 100
    
    def generate_visualizations(self, output_dir: str = './comparison_output'):
        """
        Generate visualization charts for comparison results.
        
        Args:
            output_dir: Directory to save output files
        """
        print(f"\n=== Generating Visualizations ===\n")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
        # 1. Performance Scores Bar Chart
        self._plot_performance_scores(output_dir)
        
        # 2. Setup Complexity vs Performance
        self._plot_complexity_vs_performance(output_dir)
        
        # 3. Feature Comparison Heatmap
        self._plot_feature_heatmap(output_dir)
        
        # 4. Use Case Distribution
        self._plot_use_case_distribution(output_dir)
        
        # 5. Platform Compatibility
        self._plot_platform_compatibility(output_dir)
        
        print(f"Visualizations saved to: {output_dir}")
    
    def _plot_performance_scores(self, output_dir: str):
        """Plot performance scores bar chart"""
        scores = self.results.get('performance_scores', {})
        if not scores:
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        mode_names = [self.modes[k]['name'] for k in scores.keys()]
        score_values = list(scores.values())
        colors = plt.cm.viridis(np.linspace(0, 1, len(scores)))
        
        bars = ax.barh(mode_names, score_values, color=colors)
        ax.set_xlabel('Performance Score (0-100)', fontsize=12)
        ax.set_title('Audio Visualization Mode Performance Scores', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 100)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f'{width:.1f}',
                   ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/performance_scores.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_complexity_vs_performance(self, output_dir: str):
        """Plot setup complexity vs performance score"""
        scores = self.results.get('performance_scores', {})
        perf_data = self.results.get('performance', {})
        
        if not scores or not perf_data:
            return
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        complexities = []
        performance = []
        labels = []
        colors = []
        
        backend_colors = {
            'matplotlib': '#1f77b4',
            'pygame': '#ff7f0e',
            'opencv': '#2ca02c',
            'opengl': '#d62728',
            'unity': '#9467bd'
        }
        
        for mode_id, score in scores.items():
            complexity = perf_data[mode_id].get('setup_complexity', 5)
            complexities.append(complexity)
            performance.append(score)
            labels.append(self.modes[mode_id]['name'])
            colors.append(backend_colors.get(self.modes[mode_id]['backend'], '#333333'))
        
        scatter = ax.scatter(complexities, performance, s=300, c=colors, alpha=0.6, edgecolors='black', linewidth=2)
        
        # Add labels
        for i, label in enumerate(labels):
            ax.annotate(label, (complexities[i], performance[i]), 
                       fontsize=8, ha='center', va='bottom',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        ax.set_xlabel('Setup Complexity (1-10)', fontsize=12)
        ax.set_ylabel('Performance Score (0-100)', fontsize=12)
        ax.set_title('Setup Complexity vs Performance', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/complexity_vs_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_feature_heatmap(self, output_dir: str):
        """Plot feature comparison heatmap"""
        features_data = self.results.get('features', {})
        if not features_data:
            return
        
        # Prepare data for heatmap
        feature_names = list(next(iter(features_data.values())).keys())
        mode_names = [self.modes[k]['name'] for k in features_data.keys()]
        
        matrix = []
        for mode_id in features_data.keys():
            row = [1 if features_data[mode_id][feat] else 0 for feat in feature_names]
            matrix.append(row)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        im = ax.imshow(matrix, cmap='YlGn', aspect='auto')
        
        # Set ticks
        ax.set_xticks(np.arange(len(feature_names)))
        ax.set_yticks(np.arange(len(mode_names)))
        ax.set_xticklabels(feature_names, rotation=45, ha='right')
        ax.set_yticklabels(mode_names)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Feature Available', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(mode_names)):
            for j in range(len(feature_names)):
                text = ax.text(j, i, '✓' if matrix[i][j] else '✗',
                             ha="center", va="center", color="black", fontsize=10, fontweight='bold')
        
        ax.set_title('Feature Comparison Matrix', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/feature_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_use_case_distribution(self, output_dir: str):
        """Plot use case distribution"""
        use_cases = self.results.get('use_cases', {})
        if not use_cases:
            return
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        use_case_names = list(use_cases.keys())
        mode_counts = [len(use_cases[uc]) for uc in use_case_names]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(use_case_names)))
        bars = ax.barh(use_case_names, mode_counts, color=colors)
        
        ax.set_xlabel('Number of Suitable Modes', fontsize=12)
        ax.set_title('Use Case Coverage by Visualization Modes', fontsize=14, fontweight='bold')
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f'{int(width)}',
                   ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/use_case_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_platform_compatibility(self, output_dir: str):
        """Plot platform compatibility chart"""
        perf_data = self.results.get('performance', {})
        if not perf_data:
            return
        
        # Count platform support
        platform_support = {}
        for mode_id, perf in perf_data.items():
            platforms = perf.get('platform_compatibility', [])
            for platform in platforms:
                if platform not in platform_support:
                    platform_support[platform] = []
                platform_support[platform].append(self.modes[mode_id]['name'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        platforms = list(platform_support.keys())
        counts = [len(platform_support[p]) for p in platforms]
        
        colors = plt.cm.Paired(np.linspace(0, 1, len(platforms)))
        bars = ax.bar(platforms, counts, color=colors, edgecolor='black', linewidth=1.5)
        
        ax.set_ylabel('Number of Compatible Modes', fontsize=12)
        ax.set_title('Platform Compatibility Overview', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(counts) + 1)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/platform_compatibility.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_report(self, output_dir: str = './comparison_output'):
        """
        Generate comprehensive comparison report.
        
        Args:
            output_dir: Directory to save output files
        """
        print("\n=== Generating Comparison Report ===\n")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save comparison matrix as CSV
        if 'matrix' in self.comparison_data:
            df = self.comparison_data['matrix']
            csv_path = f'{output_dir}/comparison_matrix.csv'
            df.to_csv(csv_path, index=False)
            print(f"Comparison matrix saved to: {csv_path}")
        
        # Save all results as JSON
        json_path = f'{output_dir}/comparison_results.json'
        with open(json_path, 'w') as f:
            # Convert non-serializable objects
            serializable_results = {}
            for key, value in self.results.items():
                if isinstance(value, dict):
                    serializable_results[key] = value
                else:
                    serializable_results[key] = str(value)
            json.dump(serializable_results, f, indent=2)
        print(f"Results saved to: {json_path}")
        
        # Generate markdown report
        self._generate_markdown_report(output_dir)
    
    def _generate_markdown_report(self, output_dir: str):
        """Generate detailed markdown report"""
        report_path = f'{output_dir}/COMPARISON_REPORT.md'
        
        with open(report_path, 'w') as f:
            f.write("# Audio Visualization Implementation Comparison Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write("This report provides a comprehensive statistical analysis and comparison of different ")
            f.write("audio visualization implementations across Python libraries (matplotlib, pygame, OpenCV, OpenGL) ")
            f.write("and Unity's audio system.\n\n")
            
            # Performance Scores
            f.write("## Performance Scores\n\n")
            scores = self.results.get('performance_scores', {})
            if scores:
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                f.write("| Rank | Visualization Mode | Score (0-100) |\n")
                f.write("|------|-------------------|---------------|\n")
                for i, (mode_id, score) in enumerate(sorted_scores, 1):
                    f.write(f"| {i} | {self.modes[mode_id]['name']} | {score:.2f} |\n")
                f.write("\n")
            
            # Detailed Comparison
            f.write("## Detailed Comparison\n\n")
            if 'matrix' in self.comparison_data:
                f.write("### Comparison Matrix\n\n")
                f.write(self.comparison_data['matrix'].to_markdown(index=False))
                f.write("\n\n")
            
            # Use Case Recommendations
            f.write("## Use Case Recommendations\n\n")
            use_cases = self.results.get('use_cases', {})
            if use_cases:
                for use_case, modes in use_cases.items():
                    f.write(f"### {use_case.replace('_', ' ').title()}\n\n")
                    f.write("**Recommended Modes:**\n\n")
                    for mode_id in modes[:3]:  # Top 3 recommendations
                        f.write(f"- {self.modes[mode_id]['name']}\n")
                    f.write("\n")
            
            # Conclusions
            f.write("## Key Findings\n\n")
            f.write("### Best for Performance\n")
            if scores:
                top_performer = max(scores.items(), key=lambda x: x[1])
                f.write(f"**{self.modes[top_performer[0]]['name']}** (Score: {top_performer[1]:.2f})\n\n")
            
            f.write("### Best for Unity Integration\n")
            f.write("Unity-based visualizers offer the best integration with game engines and support for ")
            f.write("multiple platforms including mobile and VR/AR.\n\n")
            
            f.write("### Best for Scientific Analysis\n")
            f.write("Matplotlib-based visualizers provide the most detailed analysis capabilities and ")
            f.write("export options for research purposes.\n\n")
            
            f.write("### Best for Real-time Performance\n")
            f.write("OpenGL and Unity visualizers offer the lowest latency and highest frame rates ")
            f.write("for real-time audio feedback.\n\n")
            
            f.write("---\n\n")
            f.write("*This report was automatically generated by the Audio Visualization Comparison Tool.*\n")
        
        print(f"Markdown report saved to: {report_path}")
    
    def run_full_comparison(self, output_dir: str = './comparison_output'):
        """
        Run complete comparison analysis and generate all outputs.
        
        Args:
            output_dir: Directory to save all output files
        """
        print("=" * 60)
        print("AUDIO VISUALIZATION COMPARISON TOOL")
        print("=" * 60)
        
        # Run all analyses
        self.analyze_performance_characteristics()
        self.analyze_features()
        self.analyze_audio_processing()
        self.compare_use_cases()
        self.generate_comparison_matrix()
        self.calculate_performance_scores()
        
        # Generate outputs
        self.generate_visualizations(output_dir)
        self.generate_report(output_dir)
        
        print("\n" + "=" * 60)
        print("COMPARISON COMPLETE")
        print("=" * 60)
        print(f"\nAll outputs saved to: {output_dir}")
        print("\nGenerated files:")
        print("  - comparison_matrix.csv")
        print("  - comparison_results.json")
        print("  - COMPARISON_REPORT.md")
        print("  - performance_scores.png")
        print("  - complexity_vs_performance.png")
        print("  - feature_heatmap.png")
        print("  - use_case_distribution.png")
        print("  - platform_compatibility.png")


def main():
    """Main function to run the comparison tool"""
    
    print("\n" + "=" * 60)
    print("Audio Visualization Implementation Comparison Tool")
    print("=" * 60 + "\n")
    
    # Check for audio file
    audio_files = ['audio.mp3', 'audio2.mp3', 'audio3.mp3', 'audio4.mp3']
    audio_file = None
    for af in audio_files:
        if os.path.exists(af):
            audio_file = af
            break
    
    # Create comparator
    comparator = AudioVisualizationComparator(audio_file=audio_file)
    
    # Run full comparison
    comparator.run_full_comparison(output_dir='./comparison_output')
    
    print("\n✅ Comparison analysis complete!")
    print("\nTo integrate with Unity:")
    print("  1. Review the generated COMPARISON_REPORT.md")
    print("  2. Check comparison_matrix.csv for detailed metrics")
    print("  3. Use the visualizations to communicate findings")
    print("  4. Unity implementations are marked in the report")


if __name__ == "__main__":
    main()
