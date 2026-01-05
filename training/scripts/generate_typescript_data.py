#!/usr/bin/env python3
"""
TypeScript Development Training Data Generator
Target: ~200 examples for TypeScript coding, types, tooling, best practices
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for TypeScript development.
You help with TypeScript coding, type system, configuration, and modern JavaScript/TypeScript best practices."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

BASIC_TS_TASKS = [
    {
        "instruction": "Initialize a new TypeScript project",
        "command": "npm init -y && npm install typescript --save-dev && npx tsc --init",
        "explanation": "Creates package.json, installs TypeScript, generates tsconfig.json"
    },
    {
        "instruction": "Compile TypeScript files",
        "command": "npx tsc",
        "explanation": "Compiles TypeScript based on tsconfig.json"
    },
    {
        "instruction": "Run TypeScript file directly",
        "command": "npx ts-node src/index.ts",
        "explanation": "Runs TypeScript without separate compile step"
    },
    {
        "instruction": "Check types without emitting files",
        "command": "npx tsc --noEmit",
        "explanation": "Type checks but doesn't generate JavaScript files"
    },
    {
        "instruction": "Watch mode for development",
        "command": "npx tsc --watch",
        "explanation": "Recompiles on file changes"
    },
    {
        "instruction": "Install type definitions for a library",
        "command": "npm install @types/node --save-dev",
        "explanation": "Installs TypeScript type definitions for Node.js"
    },
    {
        "instruction": "Run ESLint on TypeScript files",
        "command": "npx eslint 'src/**/*.ts' --fix",
        "explanation": "Lints TypeScript files and auto-fixes issues"
    },
    {
        "instruction": "Run tests with Jest and TypeScript",
        "command": "npx jest --coverage",
        "explanation": "Runs Jest tests with coverage report"
    },
    {
        "instruction": "Run TypeScript with tsx",
        "command": "npx tsx src/index.ts",
        "explanation": "Faster ts-node alternative using esbuild"
    },
    {
        "instruction": "Install ESLint for TypeScript",
        "command": "npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin",
        "explanation": "Sets up ESLint with TypeScript support"
    },
    {
        "instruction": "Install Prettier with TypeScript",
        "command": "npm install -D prettier eslint-config-prettier eslint-plugin-prettier",
        "explanation": "Adds Prettier formatting with ESLint integration"
    },
    {
        "instruction": "Generate tsconfig for Node.js",
        "command": "npx tsc --init --target ES2022 --module NodeNext --moduleResolution NodeNext",
        "explanation": "Creates tsconfig optimized for Node.js"
    },
    {
        "instruction": "Generate tsconfig for browser",
        "command": "npx tsc --init --target ES2020 --module ESNext --moduleResolution bundler",
        "explanation": "Creates tsconfig optimized for bundlers"
    },
    {
        "instruction": "Compile single file",
        "command": "npx tsc src/utils.ts --outFile dist/utils.js",
        "explanation": "Compiles specific file to JavaScript"
    },
    {
        "instruction": "Show TypeScript version",
        "command": "npx tsc --version",
        "explanation": "Displays installed TypeScript version"
    },
    {
        "instruction": "Build project with tsup",
        "command": "npx tsup src/index.ts --format cjs,esm --dts",
        "explanation": "Bundles TypeScript with CJS, ESM, and types"
    },
    {
        "instruction": "Run with experimental decorators",
        "command": "npx ts-node --compiler-options '{\"experimentalDecorators\":true}' src/index.ts",
        "explanation": "Enables decorators at runtime"
    },
]

ADVANCED_TS_TASKS = [
    {
        "instruction": "Generate TypeScript declaration files",
        "command": "npx tsc --declaration --emitDeclarationOnly",
        "explanation": "Creates .d.ts files for library publishing"
    },
    {
        "instruction": "Check for circular dependencies",
        "command": "npx madge --circular --extensions ts src/",
        "explanation": "Finds circular import dependencies"
    },
    {
        "instruction": "Build for production with esbuild",
        "command": "npx esbuild src/index.ts --bundle --minify --platform=node --outfile=dist/index.js",
        "explanation": "Fast bundling and minification"
    },
    {
        "instruction": "Analyze bundle size",
        "command": "npx source-map-explorer dist/*.js",
        "explanation": "Visualizes what's taking up space in bundle"
    },
    {
        "instruction": "Generate API documentation",
        "command": "npx typedoc --out docs src/index.ts",
        "explanation": "Creates HTML documentation from TSDoc comments"
    },
    {
        "instruction": "Check unused exports",
        "command": "npx ts-prune",
        "explanation": "Finds exported code that is never imported"
    },
    {
        "instruction": "Generate barrel exports",
        "command": "npx barrelsby --directory src --delete",
        "explanation": "Auto-generates index.ts barrel files"
    },
    {
        "instruction": "Validate JSON against TypeScript types",
        "command": "npx ts-json-schema-generator -p tsconfig.json -t Config -o schema.json",
        "explanation": "Generates JSON Schema from TypeScript type"
    },
    {
        "instruction": "Type check with strict mode",
        "command": "npx tsc --strict --noEmit",
        "explanation": "Enables all strict type checking options"
    },
    {
        "instruction": "Profile type checking performance",
        "command": "npx tsc --generateTrace trace && npx @typescript/analyze-trace trace",
        "explanation": "Generates and analyzes type checking trace"
    },
    {
        "instruction": "Upgrade TypeScript and types",
        "command": "npx typesync",
        "explanation": "Installs missing @types packages"
    },
    {
        "instruction": "Build monorepo with project references",
        "command": "npx tsc --build --verbose",
        "explanation": "Builds projects in dependency order"
    },
    {
        "instruction": "Clean TypeScript build cache",
        "command": "npx tsc --build --clean",
        "explanation": "Removes incremental build info"
    },
    {
        "instruction": "Bundle with Rollup",
        "command": "npx rollup -c rollup.config.ts --configPlugin typescript",
        "explanation": "Bundles with TypeScript config support"
    },
    {
        "instruction": "Run type coverage check",
        "command": "npx type-coverage --detail --strict",
        "explanation": "Measures percentage of typed code"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_TASKS = [
    {
        "instruction": "Create a generic Result type for error handling",
        "code": """type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

function ok<T>(data: T): Result<T, never> {
  return { success: true, data };
}

function err<E>(error: E): Result<never, E> {
  return { success: false, error };
}

// Usage
async function fetchUser(id: string): Promise<Result<User, string>> {
  try {
    const user = await api.getUser(id);
    return ok(user);
  } catch (e) {
    return err('User not found');
  }
}

// Pattern matching
const result = await fetchUser('123');
if (result.success) {
  console.log(result.data.name); // TypeScript knows data exists
} else {
  console.error(result.error); // TypeScript knows error exists
}""",
        "explanation": "Discriminated union for type-safe error handling without exceptions"
    },
    {
        "instruction": "Create a type-safe event emitter",
        "code": """type EventMap = Record<string, any>;

class TypedEventEmitter<T extends EventMap> {
  private listeners: { [K in keyof T]?: Array<(data: T[K]) => void> } = {};

  on<K extends keyof T>(event: K, listener: (data: T[K]) => void): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(listener);
  }

  off<K extends keyof T>(event: K, listener: (data: T[K]) => void): void {
    const callbacks = this.listeners[event];
    if (callbacks) {
      const index = callbacks.indexOf(listener);
      if (index > -1) callbacks.splice(index, 1);
    }
  }

  emit<K extends keyof T>(event: K, data: T[K]): void {
    this.listeners[event]?.forEach(listener => listener(data));
  }
}

// Usage
interface AppEvents {
  userLogin: { userId: string; timestamp: Date };
  dataLoaded: { items: Item[] };
  error: Error;
}

const emitter = new TypedEventEmitter<AppEvents>();
emitter.on('userLogin', (data) => {
  console.log(data.userId); // TypeScript knows the shape
});""",
        "explanation": "Generic event emitter with full type safety for event names and payloads"
    },
    {
        "instruction": "Create utility types for API responses",
        "code": """// Make all properties optional recursively
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Make specific properties required
type RequireFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Extract nested property types
type PathValue<T, P extends string> = 
  P extends `${infer K}.${infer Rest}`
    ? K extends keyof T
      ? PathValue<T[K], Rest>
      : never
    : P extends keyof T
      ? T[P]
      : never;

// API Response wrapper
interface ApiResponse<T> {
  data: T;
  meta: {
    page: number;
    total: number;
  };
}

// Unwrap response data
type UnwrapResponse<T> = T extends ApiResponse<infer U> ? U : never;

// Usage
interface User {
  id: string;
  profile: {
    name: string;
    email: string;
  };
}

type UserEmail = PathValue<User, 'profile.email'>; // string
type PartialUser = DeepPartial<User>;
type UserWithRequiredEmail = RequireFields<PartialUser, 'id'>;""",
        "explanation": "Advanced utility types for working with complex API shapes"
    },
    {
        "instruction": "Create a type-safe builder pattern",
        "code": """interface BuilderState {
  name?: string;
  age?: number;
  email?: string;
}

type RequiredKeys = 'name' | 'email';

class UserBuilder<T extends Partial<BuilderState> = {}> {
  private state: T;

  constructor(state: T = {} as T) {
    this.state = state;
  }

  name(name: string): UserBuilder<T & { name: string }> {
    return new UserBuilder({ ...this.state, name });
  }

  age(age: number): UserBuilder<T & { age: number }> {
    return new UserBuilder({ ...this.state, age });
  }

  email(email: string): UserBuilder<T & { email: string }> {
    return new UserBuilder({ ...this.state, email });
  }

  build(this: UserBuilder<{ name: string; email: string }>): User {
    return this.state as User;
  }
}

// Usage - TypeScript enforces required fields
const user = new UserBuilder()
  .name('John')
  .age(30)
  .email('john@example.com')
  .build(); // Works!

// const invalid = new UserBuilder()
//   .name('John')
//   .build(); // Error: email is required""",
        "explanation": "Builder with compile-time enforcement of required fields"
    },
    {
        "instruction": "Create exhaustive switch type guard",
        "code": """type Status = 'pending' | 'approved' | 'rejected';

// Exhaustiveness check helper
function assertNever(value: never): never {
  throw new Error(`Unexpected value: ${value}`);
}

function handleStatus(status: Status): string {
  switch (status) {
    case 'pending':
      return 'Waiting for review';
    case 'approved':
      return 'Application accepted';
    case 'rejected':
      return 'Application denied';
    default:
      // If we add a new status, TypeScript will error here
      return assertNever(status);
  }
}

// With discriminated unions
type Result =
  | { type: 'success'; data: string }
  | { type: 'error'; message: string }
  | { type: 'loading' };

function handleResult(result: Result): string {
  switch (result.type) {
    case 'success':
      return result.data; // TypeScript knows data exists
    case 'error':
      return result.message;
    case 'loading':
      return 'Loading...';
    default:
      return assertNever(result);
  }
}""",
        "explanation": "Ensures all union members are handled, catches missing cases at compile time"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up a TypeScript Node.js project with modern tooling",
        "steps": [
            "Initialize project: npm init -y",
            "Install TypeScript: npm i -D typescript @types/node",
            "Create tsconfig.json with strict settings",
            "Set up ESLint with TypeScript parser",
            "Configure Prettier for formatting",
            "Add Jest for testing with ts-jest",
            "Create src/ directory structure",
            "Add npm scripts: build, dev, test, lint",
            "Set up husky and lint-staged for pre-commit",
            "Configure VS Code settings for project"
        ]
    },
    {
        "instruction": "Migrate JavaScript project to TypeScript",
        "steps": [
            "Install TypeScript and types",
            "Create tsconfig.json with allowJs: true",
            "Rename files .js to .ts gradually",
            "Start with entry points and work inward",
            "Add types incrementally (any → specific)",
            "Fix type errors one file at a time",
            "Enable stricter checks progressively",
            "Add type definitions for dependencies",
            "Update build process",
            "Enable strict mode when ready"
        ]
    },
    {
        "instruction": "Create a type-safe API client",
        "steps": [
            "Define API endpoint types with Zod or io-ts",
            "Create response type definitions",
            "Build generic fetch wrapper with types",
            "Add request/response interceptors",
            "Implement error handling with Result type",
            "Add request cancellation support",
            "Create typed hooks if using React",
            "Add retry logic with exponential backoff",
            "Implement request caching",
            "Add comprehensive tests"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the difference between interface and type in TypeScript?",
        "answer": "Interfaces are extendable (interface A extends B), can be merged (declaration merging), and are better for object shapes. Types can represent unions, intersections, primitives, tuples - more flexible. Use interface for public API contracts (can be extended by users), type for unions and complex types. In practice, they're often interchangeable for objects. Types can use 'typeof', 'keyof', conditional types. Choose one convention and be consistent."
    },
    {
        "question": "What are generics in TypeScript?",
        "answer": "Generics allow creating reusable components that work with multiple types while maintaining type safety. Syntax: function identity<T>(arg: T): T. The type is specified at call site or inferred. Can have constraints: <T extends HasLength>. Multiple type params: <K, V>. Common uses: collections, API responses, factory functions. Built-in examples: Array<T>, Promise<T>, Map<K, V>. Think of generics as type parameters - like function parameters but for types."
    },
    {
        "question": "What is strict mode in TypeScript?",
        "answer": "strict: true in tsconfig enables all strict type checking options: strictNullChecks (null/undefined are distinct), noImplicitAny (must declare types), strictFunctionTypes (stricter function param checking), strictPropertyInitialization (class properties must be initialized), and more. Catches more bugs at compile time. New projects should use strict mode. Can enable individual flags during migration. Makes TypeScript significantly safer."
    },
    {
        "question": "What are union and intersection types?",
        "answer": "Union (A | B): value can be type A OR type B. Use for alternatives: string | number. Narrow with type guards. Intersection (A & B): value must be type A AND type B. Combines all properties: type Combined = UserProps & AdminProps. Union is 'or', intersection is 'and'. Common pattern: discriminated unions with type property for exhaustive switch statements."
    },
    {
        "question": "How do type guards work?",
        "answer": "Type guards narrow types within conditional blocks. Built-in: typeof (primitives), instanceof (classes), 'prop' in obj. Custom guards: function isString(x: unknown): x is string. After guard, TypeScript knows the narrower type. Array guards: Array.isArray(). Discriminated unions use property checks: if (result.type === 'success'). Never use type assertions (as) when guards work - guards are runtime-safe."
    },
    {
        "question": "What is the difference between any and unknown in TypeScript?",
        "answer": "Both accept any value, but unknown is safer. With 'any', you can do anything without type checking - it's an escape hatch that defeats TypeScript's purpose. With 'unknown', you must narrow the type before using it (type guard, assertion, etc.). Use unknown for values of truly unknown type (like JSON.parse result), then narrow. Use any only for migration or when interacting with legacy code."
    },
    {
        "question": "What are enums in TypeScript?",
        "answer": "Enums define named constants. Numeric enums: enum Status { Pending, Active, Done } (values 0, 1, 2). String enums: enum Status { Pending = 'PENDING' } - explicit values. Const enums are inlined at compile time for performance. Numeric enums have reverse mapping (Status[0] = 'Pending'). Modern alternative: as const objects with type inference, which some prefer for tree-shaking."
    },
    {
        "question": "What is the keyof operator in TypeScript?",
        "answer": "keyof extracts property names as a union type. type Keys = keyof User gives 'id' | 'name' | 'email'. Used in generics: function getValue<T, K extends keyof T>(obj: T, key: K): T[K]. Enables type-safe property access. Combined with typeof for object literals: keyof typeof config. Foundation for mapped types and utility types."
    },
    {
        "question": "What are readonly and const in TypeScript?",
        "answer": "const variables can't be reassigned, but object properties can change. readonly modifier on properties prevents property reassignment: readonly id: string. Readonly<T> utility makes all properties readonly. ReadonlyArray<T> for immutable arrays. as const creates deeply readonly literal types. Use readonly for immutable data structures and function parameters you don't modify."
    },
    {
        "question": "What is the never type in TypeScript?",
        "answer": "never represents values that never occur. Functions returning never: throw errors, infinite loops. Used in exhaustive checks - default case in switch that should never happen. Bottom type: assignable to everything but nothing assignable to it. Useful in conditional types: T extends U ? X : never filters types. When you see never unexpectedly, usually means impossible code path or type error."
    },
    {
        "question": "What is type inference in TypeScript?",
        "answer": "TypeScript automatically determines types without explicit annotations. Variable inference: let x = 5 (number). Return type inference from return statements. Generic inference from arguments. Array literal inference: [1, 2] is number[]. Object literal inference captures shape. Use explicit annotations for: function parameters, public API, clarity. Let TypeScript infer when the type is obvious."
    },
    {
        "question": "What are index signatures in TypeScript?",
        "answer": "Index signatures describe types of unknown property names: { [key: string]: number }. All properties must conform to signature type. Can have named properties alongside: { name: string; [key: string]: any }. Numeric indexes: { [index: number]: string } for array-like objects. Use Record<string, T> as shorthand. Be careful - makes objects accept any string key."
    },
    {
        "question": "What is the difference between null and undefined?",
        "answer": "undefined: variable declared but not assigned, missing function parameters, missing object properties. null: explicitly no value, intentional absence. With strictNullChecks, both must be handled explicitly. Use undefined for optional absence, null for intentional absence. Some prefer undefined-only to avoid confusion. Libraries may differ - match their conventions."
    },
    {
        "question": "What are type assertions in TypeScript?",
        "answer": "Type assertions tell TypeScript 'trust me, I know the type'. Syntax: value as Type or <Type>value. Doesn't change runtime behavior - compile-time only. Use when you know more than TypeScript (DOM elements, JSON parsing). Avoid when possible - prefer type guards. Double assertion for otherwise incompatible types: x as unknown as Y. Assertions can hide bugs - use sparingly."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What are mapped types?",
        "answer": "Mapped types transform properties of existing types. Syntax: { [K in keyof T]: NewType }. Built-in examples: Partial<T>, Required<T>, Readonly<T>, Pick<T, K>, Omit<T, K>. Can modify modifiers: -readonly removes readonly, +? adds optional. Template literal types enable string manipulation: `get${Capitalize<K>}`. Key remapping: { [K in keyof T as NewKey]: T[K] }. Powerful for deriving types from existing ones."
    },
    {
        "question": "What are conditional types?",
        "answer": "Conditional types select type based on condition: T extends U ? X : Y. Like ternary for types. Used in utility types: NonNullable<T> = T extends null | undefined ? never : T. With infer keyword: type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never. Can be distributive over unions. Enables complex type transformations and inference. Use for extracting or transforming types conditionally."
    },
    {
        "question": "What is declaration merging?",
        "answer": "Declaration merging combines multiple declarations with same name. Interfaces merge: two interface User declarations combine properties. Namespaces merge with functions/classes to add static properties. Module augmentation extends third-party types. Used by @types packages to extend library types. Can add properties to built-in types like Window. Be careful - can create confusing types if overused."
    },
    {
        "question": "How does TypeScript's structural typing work?",
        "answer": "TypeScript uses structural typing (duck typing) - types are compatible if they have the same shape, not the same name. Object with required properties matches interface, even without 'implements'. Enables flexibility but can cause issues: functions accepting too-wide types. Use branded types for nominal typing: type UserId = string & { __brand: 'UserId' }. Excess property checking only applies to object literals."
    },
    {
        "question": "What are template literal types?",
        "answer": "Template literal types construct string literal types: type Greeting = `Hello ${string}`. Can combine with unions: type Event = `on${EventName}`. Enables patterns like: type Getters<T> = { [K in keyof T as `get${Capitalize<K>}`]: () => T[K] }. Works with Uppercase, Lowercase, Capitalize, Uncapitalize. Used in type-safe routing, CSS-in-JS, ORM query builders. Very powerful for API consistency."
    },
    {
        "question": "What is the infer keyword in TypeScript?",
        "answer": "infer declares a type variable within conditional types to capture/extract types. Syntax: T extends SomeType<infer U> ? U : never. Examples: ReturnType<T> infers return type, Parameters<T> infers param tuple, InstanceType<T> infers class instance type. Can have multiple infers in one conditional. Powerful for extracting types from complex generics, promises, arrays, functions."
    },
    {
        "question": "What are discriminated unions?",
        "answer": "Discriminated unions (tagged unions) use a common property to distinguish between union members. type Result = { type: 'success'; data: T } | { type: 'error'; message: string }. The 'type' property is the discriminant. Switch/if on discriminant narrows to specific member. Enables exhaustive checking. Prefer over class hierarchies for data types. Pattern: common literal type property + type-specific properties."
    },
    {
        "question": "What is variance in TypeScript?",
        "answer": "Variance describes subtype relationships in generics. Covariant (out): can substitute subtypes - readonly properties, return types. Contravariant (in): can substitute supertypes - function parameters. Invariant: exact type required - mutable properties. TypeScript 4.7+ has explicit variance annotations: interface Producer<out T>. Understanding variance prevents subtle type safety issues in generic code."
    },
    {
        "question": "What are satisfies and const assertions?",
        "answer": "satisfies (TS 4.9+) validates expression matches type while preserving inference: const config = { port: 3000 } satisfies Config. Type is validated but literal types preserved. as const makes values deeply readonly with literal types: ['a', 'b'] as const has type readonly ['a', 'b'] not string[]. Combine both: const config = { ... } as const satisfies Config for validated, literal, readonly configs."
    },
    {
        "question": "How do decorators work in TypeScript?",
        "answer": "Decorators are functions that modify classes/methods/properties/parameters. Enable via experimentalDecorators. Class decorator: @Injectable() class Service. Method decorator receives target, propertyKey, descriptor. Parameter decorator adds metadata. Used heavily in Angular, NestJS. Stage 3 decorator proposal differs from experimental. TypeScript 5 supports both syntaxes. Decorators enable AOP patterns like logging, validation, dependency injection."
    },
    {
        "question": "What are type predicates?",
        "answer": "Type predicates are return type annotations that narrow types: function isString(x: unknown): x is string. When function returns true, TypeScript narrows the type in calling code. Use for custom type guards beyond typeof/instanceof. Array filter with predicate: arr.filter((x): x is NonNullable<T> => x != null). Can narrow this: method(): this is ValidState. Predicates enable type-safe runtime checks."
    },
    {
        "question": "What is module augmentation in TypeScript?",
        "answer": "Module augmentation extends types from other modules/packages. Syntax: declare module 'express' { interface Request { user: User } }. Must be in a module file (has import/export). Used to add properties to third-party types. Can augment global types: declare global { interface Window { analytics: Analytics } }. Creates type-safe extensions without modifying original packages."
    },
    {
        "question": "What are project references in TypeScript?",
        "answer": "Project references enable monorepo builds with incremental compilation. tsconfig references other tsconfigs: { references: [{ path: './lib' }] }. Use composite: true in referenced projects. tsc --build builds in dependency order. Enables faster builds - only changed projects recompile. Enforces module boundaries - can't import without reference. Good for large codebases with multiple packages."
    },
    {
        "question": "What are type-only imports/exports?",
        "answer": "Type-only imports: import type { User } from './types'. Removed at compile time - no runtime impact. Prevents accidentally importing runtime code. Required when isolatedModules: true (esbuild/swc). Can mix: import { type User, createUser } from './user'. Export type: export type { Config }. Helps bundlers tree-shake and clarifies intent."
    },
    # === EXPANDED ADVANCED CONCEPTS ===
    {
        "question": "What is the NoInfer utility type?",
        "answer": "NoInfer<T> (TS 5.4+) prevents TypeScript from inferring a type parameter from a specific position. Use: function createClient<T>(config: NoInfer<T>): Client<T>. Forces explicit type argument or inference from other positions. Useful when default inference location is wrong. Before NoInfer: workaround with conditional types. Enables more predictable generic inference patterns."
    },
    {
        "question": "What are recursive type aliases?",
        "answer": "TypeScript supports recursive type definitions: type JSONValue = string | number | boolean | null | JSONValue[] | { [key: string]: JSONValue }. Enables tree-like data structures. Recursive conditional types: type DeepReadonly<T> = { readonly [K in keyof T]: DeepReadonly<T[K]> }. Watch for 'Type instantiation is excessively deep' - add base case or explicit annotations."
    },
    {
        "question": "What are higher-order types?",
        "answer": "Higher-order types are types that operate on other types. Type functions: type Optional<T> = T | undefined. Generic constraints: <T extends HasId>. Conditional types as type-level if/else. Mapped types as type-level map. infer for pattern matching. Examples: utility types like Pick, Omit, ReturnType. Think of generics as functions and types as their arguments."
    },
    {
        "question": "What is the difference between declare and implement?",
        "answer": "declare tells TypeScript a value exists at runtime without implementation: declare const config: Config. Use for: ambient declarations, globals, modules without types. Implementation provides actual code. declare module for typing external modules. declare global for extending global types. .d.ts files are implicitly declare. Use declare when interfacing with external JavaScript."
    },
    {
        "question": "What are assertion functions?",
        "answer": "Assertion functions throw if condition fails, otherwise narrow types: function assert(condition: unknown): asserts condition. Custom assertions: function assertIsString(x: unknown): asserts x is string. After call, TypeScript knows the narrower type. Unlike type predicates (return boolean), assertions throw. Use for validation that should halt execution on failure. Works with this: asserts this is ValidState."
    },
    {
        "question": "How do I create branded/nominal types?",
        "answer": "Branded types add uniqueness to otherwise identical types: type UserId = string & { __brand: 'UserId' }. Creates type distinctions: UserId not assignable to string (directly). Constructor function validates: function UserId(s: string): UserId. Prevents mixing IDs: function getUser(id: UserId) won't accept OrderId. Pattern: primitive & { __brand: 'TypeName' }. Libraries: ts-brand, newtype-ts."
    },
    {
        "question": "What is the Extract and Exclude utility types?",
        "answer": "Extract<T, U> gets members of T assignable to U: Extract<'a' | 'b' | 'c', 'a' | 'b'> = 'a' | 'b'. Exclude<T, U> removes members assignable to U: Exclude<'a' | 'b' | 'c', 'a'> = 'b' | 'c'. Used for filtering union types. NonNullable<T> = Exclude<T, null | undefined>. Combine with keyof for property filtering. Foundation for many custom utility types."
    },
    {
        "question": "What is the Awaited utility type?",
        "answer": "Awaited<T> (TS 4.5+) unwraps Promise types recursively: Awaited<Promise<string>> = string. Awaited<Promise<Promise<number>>> = number. Used for typing async/await results. Before Awaited: complex conditional types needed. Works with PromiseLike too. Enables correct typing of Promise.all, async functions. Type-level await operator."
    },
    {
        "question": "What are type-level tests in TypeScript?",
        "answer": "Type-level tests verify type system behavior without runtime. Pattern: type Test = Expect<Equal<Actual, Expected>>. Libraries: type-testing, expect-type. Test utility types, conditional types, inference. Uses: never for invalid, specific type for valid. Example: type Assert<T extends true> = T; Assert<Equal<typeof fn, ExpectedType>>. Run with tsc --noEmit. Catch type regressions."
    },
    {
        "question": "What is excess property checking?",
        "answer": "TypeScript checks for extra properties on object literals: const x: { a: number } = { a: 1, b: 2 } // Error: 'b' not in type. Only applies to object literals, not variables. Helps catch typos and unused properties. Bypass: intermediate variable, type assertion, index signature. Structural typing allows extra props normally - excess checking is special case for literal assignments."
    },
    {
        "question": "How does this typing work in TypeScript?",
        "answer": "Functions can type 'this' as first parameter: function greet(this: User, greeting: string). Method with this type: class A { method(this: A) {...} }. Polymorphic this for fluent APIs: returns this type in subclasses. this in callbacks often needs binding or arrow functions. ThisParameterType<T> extracts this type. OmitThisParameter<T> removes this parameter from function type."
    },
    {
        "question": "What is the difference between ES modules and CommonJS in TypeScript?",
        "answer": "ES modules: import/export, static analysis, tree-shakeable. CommonJS: require/module.exports, dynamic, Node.js default. tsconfig module: 'ESNext' for modern, 'CommonJS' for Node. moduleResolution: 'node16'/'nodenext' for proper dual-module support. esModuleInterop enables default import from CJS. allowSyntheticDefaultImports for type checking only. Modern: target ESM, bundlers handle interop."
    },
    {
        "question": "What are const type parameters?",
        "answer": "const type parameters (TS 5.0+) infer narrower literal types: function make<const T>(arr: T): T. make([1, 2]) infers readonly [1, 2] not number[]. Equivalent to as const on arguments but cleaner API. Useful for configuration objects, tuples, literal inference. Pattern: builder APIs, schema definitions, type-safe configs. Reduces need for as const at call sites."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "TS2322: Type 'string' is not assignable to type 'number'",
        "error_type": "type_error",
        "response": {
            "status": "type_mismatch",
            "explanation": "Trying to assign a string where a number is expected",
            "solutions": [
                "Parse string to number: parseInt(str, 10) or Number(str)",
                "Check if the type annotation is correct",
                "Use type assertion only if you're certain: str as unknown as number",
                "Fix the source of the string value"
            ],
            "warning": "Avoid 'as' casts - they bypass type checking"
        }
    },
    {
        "instruction": "TS2339: Property 'x' does not exist on type",
        "error_type": "type_error",
        "response": {
            "status": "missing_property",
            "common_causes": [
                "Typo in property name",
                "Property not defined in type/interface",
                "Using wrong variable type",
                "Object is nullable and needs narrowing"
            ],
            "solutions": [
                "Add property to interface definition",
                "Use optional chaining: obj?.property",
                "Narrow type first: if ('x' in obj)",
                "Check type definitions are correct"
            ]
        }
    },
    {
        "instruction": "TS7006: Parameter 'x' implicitly has an 'any' type",
        "error_type": "implicit_any",
        "response": {
            "status": "needs_type_annotation",
            "explanation": "TypeScript can't infer parameter type",
            "solutions": [
                "Add type annotation: function fn(x: string)",
                "If callback, type the whole function: (x: string) => void",
                "Use generic if type varies: function fn<T>(x: T)",
                "If truly any type: function fn(x: unknown) then narrow"
            ],
            "best_practice": "Avoid 'any' - use 'unknown' and narrow with type guards"
        }
    },
    {
        "instruction": "TS2532: Object is possibly 'undefined'",
        "error_type": "nullability",
        "response": {
            "status": "needs_null_check",
            "explanation": "Value might be undefined, can't safely access properties",
            "solutions": [
                "Optional chaining: obj?.property",
                "Nullish coalescing: value ?? defaultValue",
                "Type narrowing: if (obj !== undefined)",
                "Non-null assertion (careful): obj!.property"
            ],
            "best_practice": "Handle undefined explicitly rather than asserting it away"
        }
    },
    {
        "instruction": "Type 'any' is being used too much",
        "error_type": "code_quality",
        "response": {
            "status": "anti_pattern",
            "explanation": "'any' disables type checking, defeating TypeScript's purpose",
            "alternatives": [
                "unknown: like any but requires narrowing before use",
                "Generic types for reusable components",
                "Proper interface definitions",
                "Partial<T> or DeepPartial for incomplete objects"
            ],
            "migration": "Replace any with unknown, then add type guards where used"
        }
    },
    {
        "instruction": "TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'",
        "error_type": "type_error",
        "response": {
            "status": "argument_mismatch",
            "explanation": "Function called with wrong argument type",
            "common_causes": [
                "Wrong variable passed",
                "Object missing required properties",
                "Nullable value passed to non-nullable parameter",
                "Generic type inference incorrect"
            ],
            "solutions": [
                "Check function signature and argument types",
                "Transform argument to expected type",
                "Add missing properties if object",
                "Explicitly provide generic type parameters"
            ]
        }
    },
    {
        "instruction": "TS2304: Cannot find name 'X'",
        "error_type": "reference_error",
        "response": {
            "status": "undefined_reference",
            "common_causes": [
                "Variable/type not imported",
                "Typo in name",
                "Missing type definition (@types/...)",
                "Variable not in scope"
            ],
            "solutions": [
                "Import the missing type/variable",
                "Install @types package: npm i -D @types/package",
                "Check spelling",
                "Ensure variable is declared in scope"
            ]
        }
    },
    {
        "instruction": "TS2307: Cannot find module 'X' or its type declarations",
        "error_type": "module_error",
        "response": {
            "status": "missing_module",
            "explanation": "Module not found or missing type definitions",
            "solutions": [
                "Install the package: npm install package",
                "Install types: npm install @types/package -D",
                "Create declaration file if no types exist",
                "Check moduleResolution in tsconfig.json",
                "Verify paths/baseUrl configuration"
            ],
            "workaround": "Create shim.d.ts: declare module 'package'"
        }
    },
    {
        "instruction": "TS2741: Property 'X' is missing in type but required in type 'Y'",
        "error_type": "type_error",
        "response": {
            "status": "missing_required_property",
            "explanation": "Object doesn't have all required properties",
            "solutions": [
                "Add the missing property",
                "Make property optional in interface: prop?: type",
                "Use Partial<T> if all properties should be optional",
                "Check if using correct type"
            ]
        }
    },
    {
        "instruction": "TS2551: Property 'X' does not exist. Did you mean 'Y'?",
        "error_type": "typo_error",
        "response": {
            "status": "likely_typo",
            "explanation": "TypeScript found similar property - probably a typo",
            "solutions": [
                "Use the suggested property name",
                "If intentional, add property to type definition",
                "Check for case sensitivity issues"
            ]
        }
    },
    {
        "instruction": "TS2769: No overload matches this call",
        "error_type": "overload_error",
        "response": {
            "status": "no_matching_overload",
            "explanation": "Function has multiple signatures but none match your call",
            "diagnostic_steps": [
                "Check all overload signatures",
                "Compare your argument types to each overload",
                "Look for subtle type differences"
            ],
            "solutions": [
                "Transform arguments to match an overload",
                "Provide explicit generic type parameters",
                "Cast to appropriate type if you're sure"
            ]
        }
    },
    {
        "instruction": "TS2564: Property has no initializer and is not assigned in constructor",
        "error_type": "initialization_error",
        "response": {
            "status": "uninitialized_property",
            "explanation": "Class property not assigned before use",
            "solutions": [
                "Initialize in constructor or declaration",
                "Add definite assignment assertion: prop!: type",
                "Make property optional: prop?: type",
                "Add default value: prop: type = defaultValue"
            ],
            "best_practice": "Initialize properties rather than using ! assertion"
        }
    },
    {
        "instruction": "TS2556: A spread argument must either have a tuple type or be passed to a rest parameter",
        "error_type": "spread_error",
        "response": {
            "status": "spread_type_issue",
            "explanation": "Spread operator can't be used with this array type",
            "solutions": [
                "Use 'as const' for literal arrays: [...arr] as const",
                "Type array as tuple: [string, number]",
                "Use type assertion if you know the length",
                "Restructure to not need spread"
            ]
        }
    },
    {
        "instruction": "TS2571: Object is of type 'unknown'",
        "error_type": "unknown_type",
        "response": {
            "status": "needs_narrowing",
            "explanation": "Can't use unknown value without type narrowing",
            "solutions": [
                "typeof guard: if (typeof x === 'string')",
                "instanceof guard: if (x instanceof Error)",
                "Custom type guard with type predicate",
                "Type assertion if you know the type (less safe)"
            ],
            "best_practice": "unknown requires explicit type checking before use - this is intentional for safety"
        }
    },
    {
        "instruction": "TS7053: Element implicitly has 'any' type because expression of type 'string' can't be used to index type",
        "error_type": "indexing_error",
        "response": {
            "status": "string_indexing_issue",
            "explanation": "Can't use arbitrary string to index object without index signature",
            "solutions": [
                "Add index signature: { [key: string]: ValueType }",
                "Use keyof: (obj as Record<string, unknown>)[key]",
                "Narrow to known keys: if (key in obj)",
                "Use known literal type for key"
            ]
        }
    },
    {
        "instruction": "Type instantiation is excessively deep and possibly infinite",
        "error_type": "type_complexity",
        "response": {
            "status": "recursive_type_issue",
            "explanation": "Type recursion hitting TypeScript's limit",
            "common_causes": [
                "Deeply recursive generic types",
                "Circular type references",
                "Complex conditional types"
            ],
            "solutions": [
                "Simplify the type",
                "Add explicit type annotations to break inference",
                "Use type assertion at recursion boundary",
                "Flatten recursive structure"
            ]
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": "typescript",
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    examples = []
    for task in BASIC_TS_TASKS + ADVANCED_TS_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    for task in CODE_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_code_response(task["code"], task["explanation"])
        })
    return examples

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating TypeScript Development Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} tool examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "typescript_development.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
