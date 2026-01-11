declare module 'degit' {
    interface DegitOptions {
        cache?: boolean;
        force?: boolean;
        verbose?: boolean;
    }

    interface Degit {
        clone(dest: string): Promise<void>;
    }

    export default function degit(src: string, opts?: DegitOptions): Degit;
}
