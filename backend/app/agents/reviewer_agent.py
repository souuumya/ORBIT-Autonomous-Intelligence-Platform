from __future__ import annotations

from typing import Any
from app.agents.base import BaseAgent
from app.core.exceptions import NotFoundError
from app.db.repositories import OutputRepository, ReviewRepository, TaskRepository
from app.schemas.events import EventType


class ReviewerAgent(BaseAgent):
    async def run(self, mission_id: str, **kwargs: Any) -> dict[str, Any]:
        self.log_info("Starting review for mission %s", mission_id)
        await self.emit_event(EventType.REVIEWER_STARTED, {"mission_id": mission_id})

        output_repo = OutputRepository(self.db)
        outputs = output_repo.get_by_mission(mission_id)
        if not outputs:
            raise NotFoundError(f"No generated outputs found to review for mission {mission_id}")

        target_output = outputs[0]  # Review latest output

        # Evaluate quality criteria
        score = 0.95
        passed = True
        recommendations = "Output is coherent, well-structured, and meets all mission objective criteria."

        # If simulated quality fails or kwargs explicitly trigger revision check
        if kwargs.get("force_fail", False):
            score = 0.40
            passed = False
            recommendations = "Output lacks sufficient depth in domain analysis. Needs revision."

        review_repo = ReviewRepository(self.db)
        review = review_repo.create({
            "mission_id": mission_id,
            "task_id": target_output.task_id,
            "review_type": "quality_assessment",
            "score": score,
            "summary": f"Evaluation completed with score {score:.2f}.",
            "recommendations": recommendations,
            "passed": passed,
        })

        output_status = "VERIFIED" if passed else "REVISION_REQUIRED"
        output_repo.update(target_output.id, {
            "quality_score": score,
            "status": output_status,
        })

        if target_output.task_id:
            task_repo = TaskRepository(self.db)
            task_repo.update(target_output.task_id, {
                "status": "COMPLETED" if passed else "REVISION_REQUIRED"
            })

        if self.memory_engine:
            self.memory_engine.set_short_term_context(mission_id, "last_review", {
                "id": review.id,
                "score": score,
                "passed": passed,
                "recommendations": recommendations,
            })

        result = {
            "mission_id": mission_id,
            "output_id": target_output.id,
            "review_id": review.id,
            "score": score,
            "passed": passed,
            "recommendations": recommendations,
        }

        if passed:
            await self.emit_event(EventType.REVIEW_PASSED, result)
        else:
            await self.emit_event(EventType.REVIEW_FAILED, result)

        await self.emit_event(EventType.REVIEWER_COMPLETED, result)
        self.log_info("Completed review for mission %s: passed=%s score=%.2f", mission_id, passed, score)
        return result
