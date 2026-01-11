#!/usr/bin/env node

import mri from 'mri';
import * as p from '@clack/prompts';
import pc from 'picocolors';
import { askProjectName, askTemplates, confirmSelection } from './prompts';
import { scaffoldProject } from './scaffold';

export interface CliOptions {
    projectName?: string;
    yes: boolean;
    template?: string;
    help: boolean;
}

const DEFAULT_TEMPLATES = ['github-agent', 'research-team', 'customer-workflow'];

function showHelp(): void {
    console.log(`
${pc.bold('create-agno-agent')} - Create a new Agno Agent project

${pc.bold('Usage:')}
  npx create-agno-agent [project-name] [options]

${pc.bold('Options:')}
  --yes, -y         Use default options (no prompts)
  --template, -t    Template to include
  --help, -h        Show this help message

${pc.bold('Templates:')}
  github-agent      GitHub repository analyzer agent
  research-team     Deep research multi-agent team
  customer-workflow Customer service workflow

${pc.bold('Examples:')}
  npx create-agno-agent my-project
  npx create-agno-agent my-project --yes
  npx create-agno-agent my-project --template github-agent
`);
}

function validateProjectName(name: string): string | null {
    if (!name) return 'Project name is required';
    if (!/^[a-z0-9][a-z0-9_-]*$/i.test(name)) {
        return 'Project name must start with alphanumeric and only contain letters, numbers, hyphens, and underscores';
    }
    if (name.length > 100) return 'Project name is too long (max 100 characters)';
    return null;
}

function parseArgs(argv: string[]): CliOptions {
    const args = mri(argv, {
        boolean: ['yes', 'help'],
        string: ['template'],
        alias: { y: 'yes', t: 'template', h: 'help' },
    });

    return {
        projectName: args._[0] as string | undefined,
        yes: args.yes ?? false,
        template: args.template,
        help: args.help ?? false,
    };
}

async function main(): Promise<void> {
    const options = parseArgs(process.argv.slice(2));

    if (options.help) {
        showHelp();
        return;
    }

    console.log();
    p.intro(pc.bgCyan(pc.black(' create-agno-agent ')));

    let projectName: string | undefined = options.projectName;

    if (!projectName) {
        if (options.yes) {
            p.cancel('Project name is required when using --yes');
            process.exit(1);
        }
        const nameResult = await askProjectName();
        if (p.isCancel(nameResult)) {
            p.cancel('Operation cancelled.');
            process.exit(0);
        }
        projectName = nameResult;
    } else {
        const validationError = validateProjectName(projectName);
        if (validationError) {
            p.cancel(validationError);
            process.exit(1);
        }
    }

    let selectedTemplates: string[];

    if (options.yes) {
        selectedTemplates = DEFAULT_TEMPLATES;
        p.log.info(`Using all templates: ${selectedTemplates.join(', ')}`);
    } else if (options.template) {
        const templates = Array.isArray(options.template)
            ? options.template
            : [options.template];

        const invalidTemplates = templates.filter(
            (t) => !DEFAULT_TEMPLATES.includes(t)
        );
        if (invalidTemplates.length > 0) {
            p.cancel(`Invalid template(s): ${invalidTemplates.join(', ')}`);
            process.exit(1);
        }
        selectedTemplates = templates;
    } else {
        const templatesResult = await askTemplates();
        if (p.isCancel(templatesResult)) {
            p.cancel('Operation cancelled.');
            process.exit(0);
        }
        selectedTemplates = templatesResult;
    }

    if (!options.yes) {
        const confirmed = await confirmSelection(projectName, selectedTemplates);
        if (p.isCancel(confirmed) || !confirmed) {
            p.cancel('Operation cancelled.');
            process.exit(0);
        }
    }

    await scaffoldProject(projectName, selectedTemplates);

    p.outro(
        pc.green('✓ Project created successfully!') +
        '\n\n' +
        pc.bold('Next steps:\n') +
        pc.dim(`  cd ${projectName}\n`) +
        pc.dim('  cp .env.example .env\n') +
        pc.dim('  # Edit .env with your API keys\n') +
        pc.dim('  uv sync  # or pip install -r requirements.txt\n') +
        pc.dim('  docker compose -f docker-compose.dev.yml up -d\n') +
        pc.dim('  uvicorn app.main:app --reload --port 7777\n')
    );
}

main().catch((error) => {
    p.cancel(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
});

export { parseArgs, validateProjectName };
