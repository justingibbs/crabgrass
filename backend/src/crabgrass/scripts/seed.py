"""Seed script - populate the database with sample data.

Creates sample ideas with full structure for demo purposes.
Run with: uv run python -m crabgrass.scripts.seed
"""

import logging

from crabgrass.database import init_schema
from crabgrass.syncs import register_all_syncs
from crabgrass.concepts.user import UserActions
from crabgrass.concepts.idea import IdeaActions
from crabgrass.concepts.summary import SummaryActions
from crabgrass.concepts.challenge import ChallengeActions
from crabgrass.concepts.approach import ApproachActions
from crabgrass.concepts.coherent_action import CoherentActionActions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Sample ideas with full structure
SAMPLE_IDEAS = [
    {
        "title": "Customer Reporting Improvement",
        "author": "sarah",
        "summary": (
            "Several customers have mentioned struggling with our current "
            "reporting tools. The reports take too long to generate and don't "
            "provide the insights they need to make quick decisions."
        ),
        "challenge": (
            "Our reporting system was built for a smaller customer base and "
            "doesn't scale well. Customers wait 30+ seconds for complex reports, "
            "and the data visualization is limited to basic charts."
        ),
        "approach": (
            "Implement incremental report generation with real-time updates. "
            "Start with the most-requested reports and add interactive "
            "dashboards that let customers drill down into their data."
        ),
        "actions": [
            "Audit current report generation performance bottlenecks",
            "Design new async report generation architecture",
            "Create prototype dashboard with top 3 requested reports",
        ],
    },
    {
        "title": "Mobile App Feature Gap",
        "author": "marcus",
        "summary": (
            "I noticed our mobile app is missing several key features that "
            "competitors offer. Customers have asked about offline mode and "
            "push notifications for important updates."
        ),
        "challenge": (
            "Our mobile app was launched as an MVP and hasn't received "
            "significant updates. The lack of offline capability and "
            "notifications reduces user engagement and satisfaction."
        ),
        "approach": (
            "Prioritize offline data sync as the foundation, then layer on "
            "push notifications. Focus on the 20% of features used by 80% "
            "of mobile users."
        ),
        "actions": [
            "Survey mobile users to identify top 5 missing features",
            "Implement offline data caching layer",
            "Design push notification system architecture",
        ],
    },
    {
        "title": "Onboarding Process Streamlining",
        "author": "diana",
        "summary": (
            "New customers often take weeks to get fully set up. I've heard "
            "complaints that the onboarding process has too many steps and "
            "requires too much manual configuration."
        ),
        "challenge": (
            "The onboarding process requires 15+ steps and involves multiple "
            "team members. This creates delays and frustration, especially "
            "for smaller customers who don't have dedicated IT resources."
        ),
        "approach": (
            "Create a guided onboarding wizard that automates configuration "
            "based on customer type. Use templates and smart defaults to "
            "reduce the number of decisions customers need to make."
        ),
        "actions": [
            "Map current onboarding flow and identify automation opportunities",
            "Design customer type templates (enterprise, SMB, startup)",
            "Build self-service onboarding wizard prototype",
        ],
    },
    {
        "title": "Integration with Popular Tools",
        "author": "sarah",
        "summary": (
            "Customers keep asking about integrations with Slack, Salesforce, "
            "and other tools they use daily. Right now, they have to manually "
            "copy data between systems."
        ),
        "challenge": (
            "We have a limited API but no native integrations with popular "
            "business tools. This creates friction and makes our product feel "
            "isolated from the customer's workflow."
        ),
        "approach": (
            "Build a Slack integration first (most requested), then create "
            "a Zapier connector to quickly support many other tools. Add "
            "native Salesforce integration for enterprise customers."
        ),
        "actions": [
            "Research Slack API requirements and capabilities",
            "Design bi-directional sync architecture",
            "Create Zapier triggers and actions specification",
        ],
    },
]


def get_author_id(author_name: str) -> str:
    """Get author ID by name."""
    users = UserActions.list_all()
    for user in users:
        if user.name.lower() == author_name.lower():
            return user.id
    # Fallback to Sarah
    return "sarah-001"


def seed_ideas() -> None:
    """Create sample ideas with full structure."""
    logger.info("Starting seed data creation...")

    for idea_data in SAMPLE_IDEAS:
        logger.info(f"Creating idea: {idea_data['title']}")

        # Get author ID
        author_id = get_author_id(idea_data["author"])

        # Create idea
        idea = IdeaActions.create(
            title=idea_data["title"],
            author_id=author_id,
        )
        logger.info(f"  Created idea {idea.id}")

        # Create summary (triggers embedding generation)
        summary = SummaryActions.create(
            idea_id=idea.id,
            content=idea_data["summary"],
        )
        logger.info(f"  Created summary {summary.id}")

        # Create challenge (triggers embedding generation)
        challenge = ChallengeActions.create(
            idea_id=idea.id,
            content=idea_data["challenge"],
        )
        logger.info(f"  Created challenge {challenge.id}")

        # Create approach (triggers embedding generation)
        approach = ApproachActions.create(
            idea_id=idea.id,
            content=idea_data["approach"],
        )
        logger.info(f"  Created approach {approach.id}")

        # Create actions
        for action_content in idea_data["actions"]:
            action = CoherentActionActions.create(
                idea_id=idea.id,
                content=action_content,
            )
            logger.info(f"  Created action {action.id}: {action_content[:40]}...")

        # Update idea status to Active
        IdeaActions.update(idea.id, status="Active")
        logger.info(f"  Idea set to Active")

    logger.info("Seed data creation complete!")


def main() -> None:
    """Main entry point for seed script."""
    # Initialize database
    logger.info("Initializing database...")
    init_schema()

    # Ensure mock users exist
    logger.info("Ensuring mock users exist...")
    UserActions.ensure_mock_users_exist()

    # Register syncs (so embeddings are generated)
    logger.info("Registering sync handlers...")
    register_all_syncs()

    # Check if ideas already exist
    existing_ideas = IdeaActions.list_all()
    if existing_ideas:
        logger.info(f"Found {len(existing_ideas)} existing ideas. Skipping seed.")
        return

    # Create sample ideas
    seed_ideas()

    # Verify
    ideas = IdeaActions.list_all()
    logger.info(f"Database now has {len(ideas)} ideas")


if __name__ == "__main__":
    main()
