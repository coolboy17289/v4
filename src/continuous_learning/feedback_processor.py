"""
Feedback Processor for processing user feedback
"""

import logging
from typing import Dict, Any, Optional
from .learning_engine import learning_engine

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Processes different types of user feedback"""

    def __init__(self):
        self.learning_engine = learning_engine

    def process_explicit_feedback(self, interaction_id: str, rating: int,
                                 comments: str = None,
                                 corrections: Dict[str, Any] = None) -> bool:
        """
        Process explicit feedback from users

        Args:
            interaction_id: ID of the interaction being rated
            rating: Numerical rating (typically 1-5)
            comments: Optional text comments
            corrections: Specific corrections to the output

        Returns:
            bool: True if feedback was processed successfully
        """
        try:
            feedback = {
                "rating": rating,
                "comments": comments,
                "corrections": corrections or {}
            }

            # In a real implementation, we would look up the interaction by ID
            # For now, we'll just log that we received the feedback
            logger.info(f"Processing explicit feedback for interaction {interaction_id}: {feedback}")

            # The actual processing would happen in the learning engine when
            # the interaction is retrieved from storage
            return True
        except Exception as e:
            logger.error(f"Error processing explicit feedback: {e}")
            return False

    def process_implicit_feedback(self, interaction_id: str,
                                 interaction_metrics: Dict[str, Any]) -> bool:
        """
        Process implicit feedback from user behavior

        Args:
            interaction_id: ID of the interaction
            interaction_metrics: Metrics like time_spent, scroll_depth, etc.

        Returns:
            bool: True if feedback was processed successfully
        """
        try:
            feedback = {
                "implicit": True,
                "metrics": interaction_metrics
            }

            logger.info(f"Processing implicit feedback for interaction {interaction_id}: {feedback}")
            return True
        except Exception as e:
            logger.error(f"Error processing implicit feedback: {e}")
            return False

    def process_feedback_from_dict(self, interaction_id: str,
                                  feedback_dict: Dict[str, Any]) -> bool:
        """
        Process feedback from a dictionary

        Args:
            interaction_id: ID of the interaction
            feedback_dict: Dictionary containing feedback data

        Returns:
            bool: True if feedback was processed successfully
        """
        try:
            # Extract known fields
            rating = feedback_dict.get("rating")
            comments = feedback_dict.get("comments")
            corrections = feedback_dict.get("corrections")

            if rating is not None:
                return self.process_explicit_feedback(
                    interaction_id, rating, comments, corrections
                )
            else:
                # Treat as implicit feedback
                return self.process_implicit_feedback(interaction_id, feedback_dict)
        except Exception as e:
            logger.error(f"Error processing feedback from dict: {e}")
            return False