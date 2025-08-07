"""Educational guidance and color schemes for Django Mercury.

This module provides educational content formatting and color schemes
for the interactive learning experience.
"""

from typing import Dict, Optional


class EduLiteColorScheme:
    """Color scheme for educational output following EduLite branding."""
    
    def __init__(self):
        """Initialize the EduLite color scheme."""
        # Define colors for different message types
        self.colors = {
            'success': '#75a743',  # Green
            'warning': '#de9e41',  # Orange
            'error': '#a53030',    # Red
            'info': '#4f8fba',     # Blue
            'excellent': '#73bed3', # Light blue
            'educational': '#f4c430', # Gold/yellow for learning moments
        }
        
        # ANSI color codes for terminal output
        self.ansi_colors = {
            'success': '\033[32m',    # Green
            'warning': '\033[33m',    # Yellow
            'error': '\033[31m',      # Red
            'info': '\033[34m',       # Blue
            'excellent': '\033[36m',  # Cyan
            'educational': '\033[93m', # Bright yellow
            'reset': '\033[0m',       # Reset
            'bold': '\033[1m',        # Bold
        }
    
    def colorize(self, text: str, color_type: str = 'info', bold: bool = False) -> str:
        """Apply color to text for terminal output.
        
        Args:
            text: Text to colorize
            color_type: Type of color to apply
            bold: Whether to make text bold
            
        Returns:
            Colorized text string
        """
        if color_type not in self.ansi_colors:
            return text
            
        color_code = self.ansi_colors[color_type]
        if bold:
            color_code = self.ansi_colors['bold'] + color_code
            
        return f"{color_code}{text}{self.ansi_colors['reset']}"
    
    def get_hex_color(self, color_type: str) -> Optional[str]:
        """Get hex color code for a given type.
        
        Args:
            color_type: Type of color
            
        Returns:
            Hex color code or None if not found
        """
        return self.colors.get(color_type)
    
    def format_educational_header(self, title: str) -> str:
        """Format a header for educational content.
        
        Args:
            title: Title text
            
        Returns:
            Formatted header string
        """
        border = "=" * 60
        return f"\n{self.colorize(border, 'educational')}\n{self.colorize(title, 'educational', bold=True)}\n{self.colorize(border, 'educational')}\n"
    
    def format_success_message(self, message: str) -> str:
        """Format a success message.
        
        Args:
            message: Success message text
            
        Returns:
            Formatted success message
        """
        return self.colorize(f"✅ {message}", 'success', bold=True)
    
    def format_warning_message(self, message: str) -> str:
        """Format a warning message.
        
        Args:
            message: Warning message text
            
        Returns:
            Formatted warning message
        """
        return self.colorize(f"⚠️  {message}", 'warning', bold=True)
    
    def format_error_message(self, message: str) -> str:
        """Format an error message.
        
        Args:
            message: Error message text
            
        Returns:
            Formatted error message
        """
        return self.colorize(f"❌ {message}", 'error', bold=True)
    
    def format_info_message(self, message: str) -> str:
        """Format an informational message.
        
        Args:
            message: Info message text
            
        Returns:
            Formatted info message
        """
        return self.colorize(f"ℹ️  {message}", 'info')
    
    def format_quiz_prompt(self, question: str, options: list) -> str:
        """Format a quiz question with options.
        
        Args:
            question: Quiz question text
            options: List of answer options
            
        Returns:
            Formatted quiz prompt
        """
        formatted = self.colorize("🤔 Quick Check:", 'educational', bold=True)
        formatted += f"\n{question}\n\n"
        for i, option in enumerate(options, 1):
            formatted += f"  [{i}] {option}\n"
        return formatted


class EducationalContentProvider:
    """Provides educational content for different performance issues."""
    
    def __init__(self):
        """Initialize the content provider."""
        self.content_db = {
            'n_plus_one': {
                'title': 'N+1 Query Problem',
                'explanation': 'Your code makes 1 query to get a list, then N queries for related data.',
                'impact': 'This creates N+1 total queries, making your app slow.',
                'solution': 'Use select_related() for ForeignKey or prefetch_related() for ManyToMany.',
                'example': 'User.objects.select_related("profile").all()',
            },
            'slow_response': {
                'title': 'Slow Response Time',
                'explanation': 'Your view takes too long to respond to requests.',
                'impact': 'Users experience delays and may abandon your app.',
                'solution': 'Add database indexes, optimize queries, or implement caching.',
                'example': 'class Meta:\n    indexes = [models.Index(fields=["created_at"])]',
            },
            'high_memory': {
                'title': 'High Memory Usage',
                'explanation': 'Your code loads too much data into memory at once.',
                'impact': 'Can cause server crashes and increased hosting costs.',
                'solution': 'Use iterator() for large querysets or implement pagination.',
                'example': 'Model.objects.all().iterator(chunk_size=1000)',
            },
            'missing_cache': {
                'title': 'Missing Cache Optimization',
                'explanation': 'Your code repeatedly computes the same expensive operations.',
                'impact': 'Wastes server resources and slows down responses.',
                'solution': 'Implement caching with Redis or Memcached.',
                'example': 'from django.core.cache import cache\ncache.set("key", value, 3600)',
            },
        }
    
    def get_content(self, issue_type: str) -> Dict[str, str]:
        """Get educational content for a specific issue type.
        
        Args:
            issue_type: Type of performance issue
            
        Returns:
            Dictionary with educational content
        """
        return self.content_db.get(issue_type, {
            'title': 'Performance Issue',
            'explanation': 'A performance issue was detected.',
            'impact': 'This may affect your application performance.',
            'solution': 'Review the specific issue details for guidance.',
            'example': '',
        })
    
    def format_educational_content(self, issue_type: str, color_scheme: Optional[EduLiteColorScheme] = None) -> str:
        """Format educational content for display.
        
        Args:
            issue_type: Type of performance issue
            color_scheme: Optional color scheme to use
            
        Returns:
            Formatted educational content string
        """
        if color_scheme is None:
            color_scheme = EduLiteColorScheme()
            
        content = self.get_content(issue_type)
        
        formatted = color_scheme.format_educational_header(f"📚 Learning Moment: {content['title']}")
        formatted += f"\n{color_scheme.colorize('What happened:', 'info', bold=True)}\n{content['explanation']}\n"
        formatted += f"\n{color_scheme.colorize('Why it matters:', 'warning', bold=True)}\n{content['impact']}\n"
        formatted += f"\n{color_scheme.colorize('How to fix:', 'success', bold=True)}\n{content['solution']}\n"
        
        if content['example']:
            formatted += f"\n{color_scheme.colorize('Example:', 'excellent', bold=True)}\n{content['example']}\n"
            
        return formatted