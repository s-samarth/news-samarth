"""
AI Module - LangChain/LangGraph-based News Processing

This module provides AI-powered news processing capabilities including:
- Daily summarization (ai/summarizer.py)
- Newsletter generation with AI agents (ai/newsletter.py)

Both use OpenRouter as the LLM provider and ChromaDB for storage.

Exports:
    # Summarization
    NewsSummarizer: Main summarization class
    summarize_last_24h: Convenience function for daily summarization
    
    # Newsletter Generation
    NewsletterGenerator: AI agent-based newsletter generator
    generate_newsletter: Convenience function for newsletter generation
    get_latest_newsletter: Retrieve latest newsletter
    get_newsletter_by_date: Retrieve newsletter by date
"""

from .summarizer import NewsSummarizer, summarize_last_24h
from .newsletter import (
    NewsletterGenerator,
    generate_newsletter,
    get_latest_newsletter,
    get_newsletter_by_date
)

__all__ = [
    # Summarization
    "NewsSummarizer",
    "summarize_last_24h",
    # Newsletter Generation
    "NewsletterGenerator",
    "generate_newsletter",
    "get_latest_newsletter",
    "get_newsletter_by_date"
]
