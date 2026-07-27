from polaris.agents.models import AgentAssessment, AgentDomain


def assessment_for(
    assessments: tuple[AgentAssessment, ...], domain: AgentDomain
) -> AgentAssessment:
    return next(assessment for assessment in assessments if assessment.agent_domain is domain)


def without_domain(
    assessments: tuple[AgentAssessment, ...], domain: AgentDomain
) -> tuple[AgentAssessment, ...]:
    return tuple(assessment for assessment in assessments if assessment.agent_domain is not domain)
