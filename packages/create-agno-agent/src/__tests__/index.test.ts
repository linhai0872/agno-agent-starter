import { describe, it, expect } from 'vitest';
import { parseArgs, validateProjectName } from '../index.js';

describe('parseArgs', () => {
    it('should parse project name from positional argument', () => {
        const result = parseArgs(['my-project']);
        expect(result.projectName).toBe('my-project');
        expect(result.yes).toBe(false);
        expect(result.help).toBe(false);
    });

    it('should parse --yes flag', () => {
        const result = parseArgs(['my-project', '--yes']);
        expect(result.projectName).toBe('my-project');
        expect(result.yes).toBe(true);
    });

    it('should parse -y alias for --yes', () => {
        const result = parseArgs(['my-project', '-y']);
        expect(result.yes).toBe(true);
    });

    it('should parse --template option', () => {
        const result = parseArgs(['my-project', '--template', 'github-agent']);
        expect(result.template).toBe('github-agent');
    });

    it('should parse -t alias for --template', () => {
        const result = parseArgs(['my-project', '-t', 'research-team']);
        expect(result.template).toBe('research-team');
    });

    it('should parse --help flag', () => {
        const result = parseArgs(['--help']);
        expect(result.help).toBe(true);
    });

    it('should parse -h alias for --help', () => {
        const result = parseArgs(['-h']);
        expect(result.help).toBe(true);
    });

    it('should handle empty args', () => {
        const result = parseArgs([]);
        expect(result.projectName).toBeUndefined();
        expect(result.yes).toBe(false);
        expect(result.help).toBe(false);
    });
});

describe('validateProjectName', () => {
    it('should accept valid project names', () => {
        expect(validateProjectName('my-project')).toBeNull();
        expect(validateProjectName('project123')).toBeNull();
        expect(validateProjectName('my_project')).toBeNull();
        expect(validateProjectName('MyProject')).toBeNull();
    });

    it('should reject empty names', () => {
        expect(validateProjectName('')).toBe('Project name is required');
    });

    it('should reject names starting with special characters', () => {
        expect(validateProjectName('-project')).toContain('must start with alphanumeric');
        expect(validateProjectName('_project')).toContain('must start with alphanumeric');
    });

    it('should reject names with invalid characters', () => {
        expect(validateProjectName('my project')).toContain('only contain');
        expect(validateProjectName('my.project')).toContain('only contain');
        expect(validateProjectName('my@project')).toContain('only contain');
    });

    it('should reject overly long names', () => {
        const longName = 'a'.repeat(101);
        expect(validateProjectName(longName)).toBe('Project name is too long (max 100 characters)');
    });
});
