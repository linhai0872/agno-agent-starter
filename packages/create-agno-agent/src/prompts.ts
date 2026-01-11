import * as p from '@clack/prompts';

export async function askProjectName(): Promise<string | symbol> {
    return p.text({
        message: 'What is your project name?',
        placeholder: 'my-agno-project',
        validate: (value) => {
            if (!value) return 'Project name is required';
            if (!/^[a-z0-9][a-z0-9_-]*$/i.test(value)) {
                return 'Project name must start with alphanumeric and only contain letters, numbers, hyphens, and underscores';
            }
            if (value.length > 100) return 'Project name is too long (max 100 characters)';
            return undefined;
        },
    });
}

interface TemplateOption {
    value: string;
    label: string;
    hint?: string;
}

const TEMPLATE_OPTIONS: TemplateOption[] = [
    {
        value: 'github-agent',
        label: 'GitHub Agent',
        hint: 'Repository analyzer with memory and tools',
    },
    {
        value: 'research-team',
        label: 'Research Team',
        hint: 'Multi-agent deep research coordination',
    },
    {
        value: 'customer-workflow',
        label: 'Customer Workflow',
        hint: 'Customer service workflow with RAG',
    },
];

export async function askTemplates(): Promise<string[] | symbol> {
    return p.multiselect({
        message: 'Which templates would you like to include?',
        options: TEMPLATE_OPTIONS,
        required: false,
    });
}

export async function confirmSelection(
    projectName: string,
    templates: string[]
): Promise<boolean | symbol> {
    const templateList =
        templates.length > 0 ? templates.join(', ') : 'none (blank project)';

    return p.confirm({
        message: `Create project "${projectName}" with templates: ${templateList}?`,
        initialValue: true,
    });
}
