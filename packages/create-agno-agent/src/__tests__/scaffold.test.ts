import { describe, it, expect } from 'vitest';
import { TEMPLATE_MAP, ALWAYS_REMOVE, buildInitContent } from '../scaffold.js';

describe('TEMPLATE_MAP', () => {
    it('should have correct template definitions', () => {
        expect(TEMPLATE_MAP['github-agent']).toEqual({
            dir: 'app/agents/github_analyzer',
            pattern: 'from app.agents.github_analyzer import create_github_analyzer_agent',
        });

        expect(TEMPLATE_MAP['research-team']).toEqual({
            dir: 'app/teams/deep_research',
            pattern: 'from app.teams.deep_research import create_deep_research_team',
        });

        expect(TEMPLATE_MAP['customer-workflow']).toEqual({
            dir: 'app/workflows/customer_service',
            pattern: 'from app.workflows.customer_service import create_customer_service_workflow',
        });
    });
});

describe('ALWAYS_REMOVE', () => {
    it('should include development directories', () => {
        expect(ALWAYS_REMOVE).toContain('packages');
        expect(ALWAYS_REMOVE).toContain('_bmad');
        expect(ALWAYS_REMOVE).toContain('_bmad-output');
        expect(ALWAYS_REMOVE).toContain('docs');
        expect(ALWAYS_REMOVE).toContain('example_application_dsl');
    });

    it('should include development files', () => {
        expect(ALWAYS_REMOVE).toContain('model-layer-optimization.md');
        expect(ALWAYS_REMOVE).toContain('OPENCODE_INSIGHTS.md');
    });
});

describe('buildInitContent', () => {
    const mockAgentsInit = `"""
Agent 注册入口

统一管理所有 Agent 的创建和注册。
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb


def get_all_agents(db: PostgresDb) -> list[Agent]:
    """
    获取所有 Agent 实例
    """
    agents = []

    # ============== 经典模板 Agent ==============
    from app.agents.github_analyzer import create_github_analyzer_agent

    agents.append(create_github_analyzer_agent(db))

    # ============== 添加你的 Agent ==============
    # from app.agents.your_agent.agent import create_your_agent
    # agents.append(create_your_agent(db))

    return agents


__all__ = ["get_all_agents"]
`;

    it('should keep content when template is selected', () => {
        const result = buildInitContent(mockAgentsInit, ['github-agent'], 'agents');
        expect(result).toContain('from app.agents.github_analyzer import create_github_analyzer_agent');
        expect(result).toContain('agents.append(create_github_analyzer_agent(db))');
    });

    it('should remove import and append when template is not selected', () => {
        const result = buildInitContent(mockAgentsInit, [], 'agents');
        expect(result).not.toContain('from app.agents.github_analyzer import create_github_analyzer_agent');
        expect(result).not.toContain('agents.append(create_github_analyzer_agent(db))');
    });

    it('should preserve structure and comments', () => {
        const result = buildInitContent(mockAgentsInit, [], 'agents');
        expect(result).toContain('Agent 注册入口');
        expect(result).toContain('def get_all_agents');
        expect(result).toContain('__all__ = ["get_all_agents"]');
    });
});
