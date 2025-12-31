"""Seed script - populate the database with sample data.

Creates sample ideas with full structure for demo purposes.
Run with: uv run python -m crabgrass.scripts.seed

V2 additions:
- Objectives with parent-child hierarchy
- Watches (users watching objectives)
- Idea-Objective links
- Sample notifications for demo
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
from crabgrass.concepts.objective import ObjectiveActions
from crabgrass.concepts.watch import WatchActions
from crabgrass.concepts.idea_objective import IdeaObjectiveActions
from crabgrass.concepts.notification import NotificationActions, NotificationType

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

# V2: Sample objectives with hierarchy
SAMPLE_OBJECTIVES = [
    {
        "title": "Q1 Innovation Initiative",
        "description": (
            "Drive innovation across the organization by identifying and "
            "nurturing new ideas that can improve our products and processes."
        ),
        "author": "senior",
        "children": [
            {
                "title": "Improve Customer Experience",
                "description": "Focus on reducing friction and increasing satisfaction across all customer touchpoints.",
            },
            {
                "title": "Increase Developer Productivity",
                "description": "Streamline development workflows and reduce time spent on routine tasks.",
            },
        ],
    },
    {
        "title": "Product Modernization",
        "description": (
            "Update our core product to use modern technologies and provide "
            "better integration capabilities for customers."
        ),
        "author": "senior",
        "children": [
            {
                "title": "API Enhancement",
                "description": "Expand and improve our public API to enable better third-party integrations.",
            },
            {
                "title": "Mobile Platform",
                "description": "Improve our mobile experience with offline capabilities and real-time notifications.",
            },
        ],
    },
]

# V2: Sample notifications for demo
SAMPLE_NOTIFICATIONS = [
    {
        "user": "sarah",
        "type": NotificationType.SIMILAR_FOUND,
        "message": "Found a similar idea 'Mobile App Feature Gap' (82% match to your 'Customer Reporting Improvement')",
        "source_type": "idea",
    },
    {
        "user": "mike",
        "type": NotificationType.IDEA_LINKED,
        "message": "Your idea 'Integration with Popular Tools' was linked to objective 'API Enhancement'",
        "source_type": "idea",
    },
    {
        "user": "sarah",
        "type": NotificationType.NURTURE_NUDGE,
        "message": "Your idea 'Customer Reporting Improvement' is nascent - consider adding more detail to the challenge section",
        "source_type": "idea",
    },
    {
        "user": "senior",
        "type": NotificationType.IDEA_LINKED,
        "message": "A new idea 'Onboarding Process Streamlining' was linked to your objective 'Improve Customer Experience'",
        "source_type": "objective",
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


def get_user_id(name: str) -> str:
    """Get user ID by partial name match."""
    users = UserActions.list_all()
    name_lower = name.lower()
    for user in users:
        if name_lower in user.name.lower():
            return user.id
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


def seed_objectives() -> dict[str, str]:
    """Create sample objectives with hierarchy.

    Returns a dict mapping objective titles to IDs for linking.
    """
    logger.info("Creating objectives...")
    objective_ids = {}

    for obj_data in SAMPLE_OBJECTIVES:
        author_id = get_user_id(obj_data["author"])

        # Create parent objective
        parent = ObjectiveActions.create(
            title=obj_data["title"],
            description=obj_data["description"],
            author_id=author_id,
        )
        objective_ids[parent.title] = parent.id
        logger.info(f"  Created objective: {parent.title}")

        # Create children
        for child_data in obj_data.get("children", []):
            child = ObjectiveActions.create(
                title=child_data["title"],
                description=child_data["description"],
                author_id=author_id,
                parent_id=parent.id,
            )
            objective_ids[child.title] = child.id
            logger.info(f"    Created child: {child.title}")

    logger.info(f"Created {len(objective_ids)} objectives")
    return objective_ids


def seed_watches(objective_ids: dict[str, str]) -> None:
    """Create watches for objectives."""
    logger.info("Creating watches...")

    # Senior watches all top-level objectives
    senior_id = get_user_id("senior")
    for title, obj_id in objective_ids.items():
        obj = ObjectiveActions.get_by_id(obj_id)
        if obj and not obj.parent_id:
            WatchActions.create(
                user_id=senior_id,
                target_type="objective",
                target_id=obj_id,
            )
            logger.info(f"  Senior watching: {title}")

    # Sarah watches customer experience
    sarah_id = get_user_id("sarah")
    if "Improve Customer Experience" in objective_ids:
        WatchActions.create(
            user_id=sarah_id,
            target_type="objective",
            target_id=objective_ids["Improve Customer Experience"],
        )
        logger.info("  Sarah watching: Improve Customer Experience")

    logger.info("Watches created")


def seed_idea_objective_links(objective_ids: dict[str, str]) -> None:
    """Link ideas to relevant objectives."""
    logger.info("Linking ideas to objectives...")

    ideas = IdeaActions.list_all()
    idea_by_title = {i.title: i for i in ideas}

    # Define links
    links = [
        ("Customer Reporting Improvement", "Improve Customer Experience"),
        ("Mobile App Feature Gap", "Mobile Platform"),
        ("Onboarding Process Streamlining", "Improve Customer Experience"),
        ("Integration with Popular Tools", "API Enhancement"),
    ]

    for idea_title, obj_title in links:
        idea = idea_by_title.get(idea_title)
        obj_id = objective_ids.get(obj_title)
        if idea and obj_id:
            IdeaObjectiveActions.link(idea.id, obj_id)
            logger.info(f"  Linked '{idea_title}' → '{obj_title}'")

    logger.info("Idea-objective links created")


def seed_notifications() -> None:
    """Create sample notifications for demo."""
    logger.info("Creating sample notifications...")

    ideas = IdeaActions.list_all()
    idea_by_title = {i.title: i for i in ideas}

    for notif_data in SAMPLE_NOTIFICATIONS:
        user_id = get_user_id(notif_data["user"])
        # Get a source ID from an actual idea if possible
        source_id = "demo-source"
        for idea in ideas:
            source_id = idea.id
            break

        NotificationActions.create(
            user_id=user_id,
            type=notif_data["type"],
            message=notif_data["message"],
            source_type=notif_data["source_type"],
            source_id=source_id,
        )
        logger.info(f"  Created notification for {notif_data['user']}")

    logger.info("Sample notifications created")


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

    # V2: Create objectives, watches, and links
    objective_ids = seed_objectives()
    seed_watches(objective_ids)
    seed_idea_objective_links(objective_ids)
    seed_notifications()

    # Verify
    ideas = IdeaActions.list_all()
    objectives = ObjectiveActions.list_all()
    notifications = NotificationActions.list_all()
    logger.info(f"Database now has {len(ideas)} ideas, {len(objectives)} objectives, {len(notifications)} notifications")


if __name__ == "__main__":
    main()
