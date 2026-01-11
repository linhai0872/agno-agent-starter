import * as p from '@clack/prompts';
import degit from 'degit';
import { existsSync, promises as fs } from 'node:fs';
import { join } from 'node:path';
import pc from 'picocolors';

const REPO_SOURCE = 'linhai0872/agno-agent-starter';

const ALWAYS_REMOVE = [
    'packages',
    '_bmad',
    '_bmad-output',
    'docs',
    'example_application_dsl',
    'model-layer-optimization.md',
    'OPENCODE_INSIGHTS.md',
    'app/agents/.gitkeep',
    'app/teams/.gitkeep',
    'app/workflows/.gitkeep',
];

const TEMPLATE_MAP: Record<string, { dir: string; pattern: string }> = {
    'github-agent': {
        dir: 'app/agents/github_analyzer',
        pattern: 'from app.agents.github_analyzer import create_github_analyzer_agent',
    },
    'research-team': {
        dir: 'app/teams/deep_research',
        pattern: 'from app.teams.deep_research import create_deep_research_team',
    },
    'customer-workflow': {
        dir: 'app/workflows/customer_service',
        pattern: 'from app.workflows.customer_service import create_customer_service_workflow',
    },
};


async function removePathIfExists(targetDir: string, relativePath: string): Promise<void> {
    const fullPath = join(targetDir, relativePath);
    if (existsSync(fullPath)) {
        await fs.rm(fullPath, { recursive: true, force: true });
    }
}

async function removeDevelopmentFiles(targetDir: string): Promise<void> {
    for (const path of ALWAYS_REMOVE) {
        await removePathIfExists(targetDir, path);
    }
}

async function removeUnselectedTemplates(
    targetDir: string,
    selectedTemplates: string[]
): Promise<void> {
    const allTemplates = Object.keys(TEMPLATE_MAP);
    const unselectedTemplates = allTemplates.filter(
        (t) => !selectedTemplates.includes(t)
    );

    for (const template of unselectedTemplates) {
        const { dir } = TEMPLATE_MAP[template];
        await removePathIfExists(targetDir, dir);
    }
}

function buildInitContent(
    originalContent: string,
    selectedTemplates: string[],
    category: 'agents' | 'teams' | 'workflows'
): string {
    const allTemplates: Record<string, string[]> = {
        agents: ['github-agent'],
        teams: ['research-team'],
        workflows: ['customer-workflow'],
    };

    const unselected = allTemplates[category].filter(
        (t) => !selectedTemplates.includes(t)
    );

    let content = originalContent;

    for (const template of unselected) {
        const { pattern } = TEMPLATE_MAP[template];

        // Remove import line
        const importRegex = new RegExp(`\\s*${escapeRegex(pattern)}.*\\n`, 'g');
        content = content.replace(importRegex, '\n');

        // Remove append line (e.g., "agents.append(create_github_analyzer_agent(db))")
        const funcName = pattern.split('import ')[1];
        if (funcName) {
            const appendRegex = new RegExp(`\\s*\\w+\\.append\\(${funcName}\\(db\\)\\).*\\n`, 'g');
            content = content.replace(appendRegex, '\n');
        }
    }

    // Clean up multiple blank lines
    content = content.replace(/\n{3,}/g, '\n\n');

    return content;
}

function escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function updateRegistryFiles(
    targetDir: string,
    selectedTemplates: string[]
): Promise<void> {
    const registryUpdates: Array<{ file: string; category: 'agents' | 'teams' | 'workflows' }> = [
        { file: 'app/agents/__init__.py', category: 'agents' },
        { file: 'app/teams/__init__.py', category: 'teams' },
        { file: 'app/workflows/__init__.py', category: 'workflows' },
    ];

    for (const { file, category } of registryUpdates) {
        const filePath = join(targetDir, file);
        if (!existsSync(filePath)) continue;

        const originalContent = await fs.readFile(filePath, 'utf-8');
        const newContent = buildInitContent(originalContent, selectedTemplates, category);

        if (newContent !== originalContent) {
            await fs.writeFile(filePath, newContent, 'utf-8');
        }
    }
}

async function cleanPycache(targetDir: string): Promise<void> {
    const dirs = ['app/agents/__pycache__', 'app/teams/__pycache__', 'app/workflows/__pycache__'];
    for (const dir of dirs) {
        await removePathIfExists(targetDir, dir);
    }
}

export async function scaffoldProject(
    projectName: string,
    selectedTemplates: string[]
): Promise<void> {
    const targetDir = join(process.cwd(), projectName);

    if (existsSync(targetDir)) {
        const overwrite = await p.confirm({
            message: `Directory "${projectName}" already exists. Overwrite?`,
            initialValue: false,
        });

        if (p.isCancel(overwrite) || !overwrite) {
            throw new Error('Directory already exists');
        }

        await fs.rm(targetDir, { recursive: true, force: true });
    }

    const spinner = p.spinner();
    spinner.start('Cloning template repository...');

    try {
        const emitter = degit(REPO_SOURCE, { cache: false, force: true });
        await emitter.clone(targetDir);
        spinner.stop('Template cloned');
    } catch (error) {
        spinner.stop('Clone failed');
        const message = error instanceof Error ? error.message : String(error);

        if (message.includes('ENOTFOUND') || message.includes('network')) {
            throw new Error(
                `Network error: Unable to fetch template. Please check your internet connection and try again.\n  Details: ${message}`
            );
        }

        throw new Error(`Failed to clone template: ${message}`);
    }

    spinner.start('Cleaning up development files...');
    await removeDevelopmentFiles(targetDir);
    spinner.stop('Development files removed');

    if (selectedTemplates.length < Object.keys(TEMPLATE_MAP).length) {
        spinner.start('Removing unselected templates...');
        await removeUnselectedTemplates(targetDir, selectedTemplates);
        await updateRegistryFiles(targetDir, selectedTemplates);
        spinner.stop('Templates configured');
    }

    spinner.start('Final cleanup...');
    await cleanPycache(targetDir);
    spinner.stop('Cleanup complete');

    p.log.success(pc.green(`Project created at ${pc.bold(targetDir)}`));

    if (selectedTemplates.length === 0) {
        p.log.info(
            pc.dim(
                'Created blank project. Add your agents to app/agents/, teams to app/teams/, and workflows to app/workflows/'
            )
        );
    } else {
        p.log.info(
            pc.dim(`Included templates: ${selectedTemplates.join(', ')}`)
        );
    }
}

export {
    TEMPLATE_MAP,
    ALWAYS_REMOVE,
    removeDevelopmentFiles,
    removeUnselectedTemplates,
    buildInitContent,
};
