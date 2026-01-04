#!/usr/bin/env python3
"""
Generate general programming concepts and best practices training data.
Covers design patterns, code quality, refactoring, and programming principles.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

SYSTEM_PROMPT = "You are AJ, an AI coding assistant. You are helping with general programming concepts and best practices."

# =============================================================================
# DESIGN PATTERNS
# =============================================================================

DESIGN_PATTERNS = [
    {
        "question": "What is the Singleton pattern and when should I use it?",
        "answer": "Singleton ensures only one instance of a class exists. Implementation: private constructor, static instance getter. Use for: database connections, configuration, logging. Problems: global state (hard to test), hidden dependencies, threading issues. Better alternatives: dependency injection, passing instance explicitly. If you must use: lazy initialization, thread-safe implementation. Python: use module-level instance (modules are singletons). Avoid in most cases - consider if you really need exactly one instance."
    },
    {
        "question": "What is the Factory pattern?",
        "answer": "Factory creates objects without specifying exact class. Types: Simple Factory (static method), Factory Method (subclasses decide), Abstract Factory (family of objects). Use when: creation is complex, need to decouple creation from usage, different implementations for same interface. Example: ConnectionFactory creating MySQL/PostgreSQL connections. Benefits: centralized creation logic, easy to swap implementations. In Python: often just functions or classmethods. DI containers are essentially factories."
    },
    {
        "question": "What is the Strategy pattern?",
        "answer": "Strategy encapsulates interchangeable algorithms. Components: Context (uses strategy), Strategy interface, Concrete strategies. Example: sorting algorithms, payment methods, compression formats. Benefits: open/closed principle (add strategies without modifying context), runtime algorithm selection. Implementation: interface/abstract class with method, inject into context. Python: often just pass functions (first-class functions). Use when: multiple algorithms for same task, need to switch at runtime."
    },
    {
        "question": "What is the Observer pattern?",
        "answer": "Observer defines one-to-many dependency - when subject changes, observers are notified. Components: Subject (maintains observer list), Observer (defines update interface). Use for: event systems, UI updates, pub/sub. Push vs pull: push sends data with notification, pull lets observers query. Benefits: loose coupling between subject and observers. Modern alternatives: reactive streams, event emitters, signals. JavaScript: EventEmitter, DOM events. Python: signals in Django, callbacks."
    },
    {
        "question": "What is the Decorator pattern?",
        "answer": "Decorator adds behavior to objects dynamically without inheritance. Components: Component interface, Concrete component, Decorator (wraps component). Example: adding logging, caching, authentication to services. Benefits: composition over inheritance, single responsibility, add/remove features at runtime. Python: @decorator syntax is different but related concept. Java: InputStream decorators (BufferedInputStream wraps FileInputStream). Use when: need to extend behavior optionally, want to avoid subclass explosion."
    },
    {
        "question": "What is the Repository pattern?",
        "answer": "Repository abstracts data access, providing collection-like interface for domain objects. Methods: find, findById, save, delete. Benefits: domain code doesn't know about database, easy to swap persistence (SQL to NoSQL), testable with in-memory implementation. Not just CRUD wrapper - can encapsulate complex queries. Related: Unit of Work (tracks changes, batches saves). ORM repositories: many ORMs provide this. Keep repositories focused on aggregate roots."
    },
    {
        "question": "What is Dependency Injection?",
        "answer": "DI provides dependencies to objects rather than having them create dependencies. Types: constructor injection (preferred), setter injection, interface injection. Benefits: testable (inject mocks), flexible (swap implementations), explicit dependencies. Containers: Spring, .NET DI, Angular, Python's inject library. Manual DI: just pass dependencies in constructor. Composition root: wire dependencies at app entry point. Avoid: service locator (hidden dependencies). Makes code more modular and testable."
    },
    {
        "question": "What is the Builder pattern?",
        "answer": "Builder separates object construction from representation, allowing step-by-step creation. Use for: complex objects with many parameters, immutable objects, avoiding telescoping constructors. Implementation: Builder class with setter methods returning self, build() method creates object. Fluent interface: method chaining for readability. Example: StringBuilder, HttpRequestBuilder. In Python: often replaced by dataclasses with default values, or keyword arguments. Use when construction logic is complex."
    },
    {
        "question": "What is the Command pattern?",
        "answer": "Command encapsulates request as object, enabling parameterization, queuing, logging, and undo. Components: Command (interface with execute), Concrete commands, Invoker (triggers command), Receiver (performs action). Use for: undo/redo, job queues, macro recording, transactions. Benefits: decouple invocation from execution, commands are first-class objects. Related: Event Sourcing stores commands as events. Example: menu items, keyboard shortcuts, task schedulers."
    },
    {
        "question": "What is the Adapter pattern?",
        "answer": "Adapter converts interface of a class to interface client expects. Use for: integrating incompatible interfaces, wrapping legacy code, third-party library integration. Types: object adapter (composition, preferred), class adapter (inheritance). Example: adapting XML parser to JSON interface, database driver adapters. Benefits: reuse existing code, isolate changes. Related: Facade (simplifies complex interface), Bridge (separates abstraction from implementation). Keep adapters thin."
    },
]

# =============================================================================
# SOLID PRINCIPLES
# =============================================================================

SOLID_PRINCIPLES = [
    {
        "question": "What are the SOLID principles?",
        "answer": "SOLID: five principles for maintainable OOP code.\n\n**S - Single Responsibility**: Class has one reason to change\n**O - Open/Closed**: Open for extension, closed for modification\n**L - Liskov Substitution**: Subtypes must be substitutable for base types\n**I - Interface Segregation**: Many specific interfaces over one general\n**D - Dependency Inversion**: Depend on abstractions, not concretions\n\nThese principles reduce coupling, improve testability, and make code easier to change. Apply pragmatically, not dogmatically."
    },
    {
        "question": "What is the Single Responsibility Principle?",
        "answer": "SRP: A class should have one reason to change (one responsibility). Signs of violation: class has multiple unrelated methods, changes for different reasons, hard to name concisely. Example: UserService handling auth AND email - split into AuthService and EmailService. Benefits: smaller classes, easier testing, clear purpose. Not about doing one thing, but changing for one reason. Find boundaries: what might change independently? Consider actors: who requires changes?"
    },
    {
        "question": "What is the Open/Closed Principle?",
        "answer": "OCP: Open for extension, closed for modification. Add new behavior without changing existing code. Achieve via: inheritance, composition, strategy pattern, plugins. Example: adding new payment method shouldn't modify existing payment code - use PaymentStrategy interface. Benefits: reduces regression risk, enables parallel development. Not absolute: sometimes modification is simpler. Apply when: code is stable and needs extension points. Don't over-engineer for hypothetical extensions."
    },
    {
        "question": "What is the Liskov Substitution Principle?",
        "answer": "LSP: Subtypes must be substitutable for their base types without breaking behavior. Violations: subclass throws unexpected exceptions, changes preconditions/postconditions, breaks invariants. Classic example: Square shouldn't extend Rectangle (setting width affects height unexpectedly). Tests: can client code work with any subtype? Check: method signatures, exception types, state invariants. Prefer composition over inheritance to avoid violations."
    },
    {
        "question": "What is the Interface Segregation Principle?",
        "answer": "ISP: Clients shouldn't depend on methods they don't use. Large interfaces force implementing unnecessary methods. Solution: break into smaller, focused interfaces. Example: instead of Worker interface with work() and eat(), use Workable and Feedable. Benefits: reduced coupling, easier implementation, clearer contracts. Signs of violation: interfaces with many methods, implementers with stub/throw implementations. Consider: role interfaces based on client needs."
    },
    {
        "question": "What is the Dependency Inversion Principle?",
        "answer": "DIP: High-level modules shouldn't depend on low-level modules; both should depend on abstractions. Don't: UserService depends directly on MySQLDatabase. Do: UserService depends on UserRepository interface, MySQLUserRepository implements it. Benefits: testable (mock the abstraction), flexible (swap implementations), decoupled. Combined with Dependency Injection: abstractions injected at runtime. Applies to modules, packages, layers - not just classes."
    },
]

# =============================================================================
# CODE QUALITY
# =============================================================================

CODE_QUALITY = [
    {
        "question": "What makes code readable?",
        "answer": "Readability factors: meaningful names (intent-revealing), small functions (single purpose), consistent formatting, clear control flow, minimal nesting. Comments: explain why, not what (code should show what). Structure: organize by feature or layer, keep related code together. Avoid: abbreviations, magic numbers, deep nesting, long parameter lists. Read code more than write - optimize for reading. Team standards: consistent style, enforced by linters. Readable code is maintainable code."
    },
    {
        "question": "When should I refactor code?",
        "answer": "Refactor when: adding features (prepare code), fixing bugs (understand then improve), code review (while context is fresh). Rule of three: refactor on third duplication. Boy Scout Rule: leave code better than you found it. Red flags: long methods, large classes, duplicated code, complex conditions, feature envy. Don't: refactor without tests, mix with feature changes, refactor working code just because. Small, incremental refactorings are safer than big rewrites."
    },
    {
        "question": "What is technical debt?",
        "answer": "Technical debt: shortcuts that make future changes harder. Types: intentional (deadline pressure, known tradeoffs) vs unintentional (lack of knowledge), prudent vs reckless. Examples: missing tests, hardcoded values, poor architecture, outdated dependencies. Costs: slower development, more bugs, harder onboarding. Managing: track in backlog, pay down incrementally, allocate capacity (20% rule). Not all debt is bad: conscious shortcuts for learning. Compound interest: ignoring makes it worse."
    },
    {
        "question": "What is code smell?",
        "answer": "Code smell: surface indication of deeper problem. Common smells: Long Method, Large Class, Feature Envy (method uses other class more than own), Data Clumps (same data groups together), Primitive Obsession, Switch Statements, Parallel Inheritance, Speculative Generality, Temporary Field, Message Chains, Middle Man. Detection: static analysis, code review, feeling of friction. Smells indicate: maybe refactor, investigate further. Not all smells require fixing."
    },
    {
        "question": "How do I write maintainable code?",
        "answer": "Maintainable code: easy to understand, change, and fix. Principles: single responsibility, low coupling, high cohesion, DRY (Don't Repeat Yourself). Practices: small functions, meaningful names, consistent style, comprehensive tests, documentation of why. Architecture: clear boundaries, explicit dependencies, separation of concerns. Team: code review, pair programming, knowledge sharing. Avoid: premature optimization, over-engineering, clever code. Write for the next developer (including future you)."
    },
    {
        "question": "What is coupling and cohesion?",
        "answer": "Coupling: degree of interdependence between modules. Low coupling is better - changes don't ripple. Types: content (worst), common, control, stamp, data (best). Cohesion: how related elements within a module are. High cohesion is better - module does one thing well. Types: coincidental (worst), logical, temporal, procedural, communicational, sequential, functional (best). Goal: low coupling, high cohesion. Achieve via: clear interfaces, dependency injection, proper boundaries."
    },
    {
        "question": "How do I handle error handling properly?",
        "answer": "Error handling principles: fail fast (detect early), fail loudly (don't swallow exceptions), fail gracefully (user-friendly messages). Use exceptions for exceptional conditions, not control flow. Catch specific exceptions, not generic. Include context in error messages. Log errors with stack traces. Create custom exceptions for domain errors. Don't: catch and ignore, catch too broadly, use exceptions for validation. Return early on errors. Consider: Result types, Option types for expected absence."
    },
    {
        "question": "What is the DRY principle?",
        "answer": "DRY: Don't Repeat Yourself - every piece of knowledge has single, unambiguous representation. Not just about code duplication: duplicated knowledge in different forms counts. Apply: extract functions, use constants, abstract common patterns. But: not all similar code is duplication (accidental similarity). Premature DRYing creates wrong abstractions. Rule of three: wait for third occurrence. WET (Write Everything Twice) is OK while learning. DRY between layers, not within."
    },
]

# =============================================================================
# REFACTORING TECHNIQUES
# =============================================================================

REFACTORING = [
    {
        "question": "What is Extract Method refactoring?",
        "answer": "Extract Method: take code fragment, turn into method with name explaining purpose. When: code is too long, needs comment to explain, duplicated logic. Steps: identify code to extract, check for local variables used (become parameters or return values), create new method, replace original with call. Benefits: shorter methods, reusable code, self-documenting names. IDE support: most IDEs automate this. Most common and valuable refactoring."
    },
    {
        "question": "What is Extract Class refactoring?",
        "answer": "Extract Class: split a class that does too much. Signs: class has too many responsibilities, subsets of fields/methods go together, hard to name class. Steps: identify data and methods that belong together, create new class, move fields and methods, update references. Example: User class with address fields → User + Address classes. Related: Extract Superclass, Extract Interface. Improves: single responsibility, cohesion."
    },
    {
        "question": "What is Replace Conditional with Polymorphism?",
        "answer": "Replace Conditional with Polymorphism: switch/if statements on type → subclasses with overridden methods. When: conditional logic on type repeated throughout code. Steps: create subclass for each case, move conditional branch to overriding method, replace conditional with polymorphic call. Example: Shape.draw() with if (type == CIRCLE) → Circle.draw(), Square.draw(). Benefits: open/closed principle, no type checking scattered. Consider: strategy pattern if behavior varies independently."
    },
    {
        "question": "What is Introduce Parameter Object?",
        "answer": "Introduce Parameter Object: group related parameters into single object. When: same parameters passed together repeatedly, methods have many parameters. Steps: create class holding parameters, replace parameters with object, add behavior to new class if appropriate. Example: (startDate, endDate) → DateRange. Benefits: cleaner signatures, single place for validation, can add methods. Data clump smell: if same data travels together, it belongs together."
    },
    {
        "question": "What is Replace Magic Number with Constant?",
        "answer": "Replace Magic Number with Constant: unexplained literal → named constant. Why: literals don't explain purpose, easy to mistype, hard to change. Steps: create constant with descriptive name, replace all occurrences. Example: if (status == 3) → if (status == STATUS_APPROVED). Apply to: numbers, strings, any literal with meaning. Enum types: often better than constants for related values. Configuration: runtime-changeable values separate from code constants."
    },
    {
        "question": "What is Move Method refactoring?",
        "answer": "Move Method: method uses more of another class's data than its own (feature envy). Steps: identify target class, check for references to current class, move method, update callers. Example: Order.calculateTax() using only Customer data → Customer.calculateTax(order). Benefits: improved cohesion, reduced coupling. Consider: delegation if method still needs some original class data. Sometimes: create new class for method."
    },
    {
        "question": "What is Rename refactoring?",
        "answer": "Rename: change name of variable, function, class to better express intent. Most common refactoring. When: name doesn't reflect purpose, name is abbreviated, understanding improved. How: use IDE rename (updates all references), search for string usages (logs, configs). Good names: intention-revealing, pronounceable, consistent. Rename when you learn more about the domain. Don't be afraid to rename: meaning is more important than typing. API consideration: public names need deprecation path."
    },
]

# =============================================================================
# PROGRAMMING CONCEPTS
# =============================================================================

PROGRAMMING_CONCEPTS = [
    {
        "question": "What is recursion and when should I use it?",
        "answer": "Recursion: function calls itself. Components: base case (stops recursion), recursive case (calls self with smaller problem). Use for: tree traversal, divide and conquer, mathematical sequences, problems naturally defined recursively. Downsides: stack overflow for deep recursion, can be harder to understand, often slower than iteration. Optimization: tail recursion (some languages optimize), memoization. Convert to iteration if: performance critical, deep recursion, simpler iteratively. Think recursively, implement iteratively if needed."
    },
    {
        "question": "What is Big O notation?",
        "answer": "Big O describes algorithm scalability as input grows. Common complexities: O(1) constant, O(log n) logarithmic, O(n) linear, O(n log n) linearithmic, O(n^2) quadratic, O(2^n) exponential. Focus on: worst case, dominant terms (drop constants and lower terms). Examples: array access O(1), binary search O(log n), linear search O(n), nested loops O(n^2). Space complexity: memory used. Trade-offs: time vs space. Premature optimization is evil, but know your algorithm's complexity."
    },
    {
        "question": "What is immutability and why does it matter?",
        "answer": "Immutability: objects cannot be changed after creation. Benefits: thread-safe (no shared mutable state), predictable (no unexpected changes), cacheable (same input = same object), undo-friendly (keep old versions). Implementation: don't expose setters, return new objects on change, use const/final, deep immutability for nested objects. Languages: functional languages default immutable. Use for: value objects, configuration, concurrent code. Cost: more object creation (often optimized). When mutation needed: local mutation, builder pattern."
    },
    {
        "question": "What is composition over inheritance?",
        "answer": "Composition: build complex objects by combining simpler ones (has-a). Inheritance: define new class based on existing (is-a). Prefer composition because: more flexible, avoids deep hierarchies, easier to change, supports multiple behaviors. Inheritance problems: tight coupling, fragile base class, limits to single parent (usually). Use inheritance for: true is-a relationships, template method pattern, framework extension points. Use composition for: behaviors, strategies, decorating. Favor interfaces for type relationships."
    },
    {
        "question": "What is null safety and how do I handle nulls?",
        "answer": "Null problems: NullPointerException, null checks everywhere, unclear if null is valid. Solutions: Optional/Maybe types (wrap potentially absent values), null object pattern (return empty implementation), assertions/contracts. Language support: Kotlin's null safety, TypeScript strict null checks, C# nullable reference types. Strategies: avoid returning null, use empty collections instead, fail fast on null parameters. Document: clearly state if null is valid. Prefer: return Optional<T> over T that might be null."
    },
    {
        "question": "What is the difference between concurrency and parallelism?",
        "answer": "Concurrency: dealing with multiple things at once (structure). Parallelism: doing multiple things at once (execution). Concurrency without parallelism: single CPU, time-slicing. Parallelism without concurrency: SIMD, same operation on multiple data. Concurrent programming: threads, async/await, actors, channels. Challenges: race conditions, deadlocks, shared state. Solutions: immutability, message passing, locks/mutexes. Async != parallel: async is about not blocking, can be single-threaded."
    },
    {
        "question": "What is defensive programming?",
        "answer": "Defensive programming: assume code will be misused or environment hostile. Techniques: validate inputs, check preconditions, handle errors gracefully, fail fast, use assertions. Don't trust: user input, external systems, method parameters. Validate: types, ranges, formats, lengths. Benefits: bugs found early, clearer error messages, more robust. Balance: don't check everything everywhere (trust established contracts within system). Public API: always validate. Internal: trust but verify."
    },
    {
        "question": "What are pure functions?",
        "answer": "Pure functions: same inputs always produce same output, no side effects. Characteristics: deterministic, no external state access, no I/O. Benefits: easy to test, cacheable/memoizable, parallelizable, easier to reason about. Side effects: database writes, API calls, modifying external state, logging. Functional core/imperative shell: pure logic in core, side effects at edges. Not all functions can be pure, but maximize pure code. Pure + immutable = predictable, testable code."
    },
]

# =============================================================================
# ALGORITHMS & DATA STRUCTURES
# =============================================================================

ALGORITHMS = [
    {
        "question": "When should I use different data structures?",
        "answer": "Array/List: ordered, indexed access O(1), search O(n), insert/delete O(n). LinkedList: ordered, fast insert/delete O(1) at known position, slow access O(n). HashMap/Dict: key-value lookup O(1) average, no order (or insertion order in modern versions). Set: unique values, membership test O(1). Stack: LIFO, push/pop O(1). Queue: FIFO, enqueue/dequeue O(1). Tree: hierarchical, sorted if BST. Heap: priority access O(1), insert O(log n). Choose based on operations needed most."
    },
    {
        "question": "How do hash tables work?",
        "answer": "Hash table: key-value storage with O(1) average access. Process: hash function converts key to index, store value at index. Collisions: multiple keys hash to same index. Resolution: chaining (linked list at each index), open addressing (probe next slot). Load factor: elements/buckets, affects performance. Rehashing: grow table when load factor high. Good hash functions: uniform distribution, fast. Python dict, Java HashMap, JS objects/Map. Understanding helps with performance optimization."
    },
    {
        "question": "What sorting algorithms should I know?",
        "answer": "QuickSort: O(n log n) average, O(n^2) worst, in-place. Good general purpose. MergeSort: O(n log n) always, stable, needs extra space. Good for linked lists. HeapSort: O(n log n), in-place, not stable. TimSort: hybrid merge+insertion, used by Python/Java. O(n log n), stable, adaptive. Comparison sorts can't beat O(n log n). Non-comparison: counting sort, radix sort for specific cases. In practice: use built-in sort (usually TimSort), only implement for learning."
    },
    {
        "question": "What is memoization?",
        "answer": "Memoization: cache function results to avoid recomputation. Use for: expensive pure functions, recursive algorithms (Fibonacci). Implementation: store results in map (args → result), check cache before computing. Python: @functools.lru_cache decorator. Benefits: can turn exponential recursive algorithms into polynomial. Considerations: memory usage, cache invalidation, only works for pure functions. Related: dynamic programming (bottom-up), caching (more general). Trade-off: space for time."
    },
    {
        "question": "What is binary search?",
        "answer": "Binary search: find element in sorted array by repeatedly dividing in half. O(log n) time. Process: compare with middle, if target smaller search left half, if larger search right half. Requirements: sorted data, random access. Variations: find first/last occurrence, find insert position, search in rotated array. Common errors: integer overflow in mid calculation, off-by-one in bounds. Standard library: use built-in (Python bisect, Java Collections.binarySearch). Applies to: any monotonic condition, not just arrays."
    },
    {
        "question": "What is a tree data structure?",
        "answer": "Tree: hierarchical structure with root, nodes, and leaves. Types: binary tree (max 2 children), BST (sorted), balanced (AVL, Red-Black), B-tree (databases), trie (prefix matching). Traversals: DFS (preorder, inorder, postorder), BFS (level order). Use for: hierarchical data (filesystems, DOM), searching (BST), autocomplete (trie). BST operations O(log n) if balanced, O(n) if skewed. Balanced trees guarantee O(log n). Heap is special tree for priority queues."
    },
    {
        "question": "What is a graph data structure?",
        "answer": "Graph: nodes (vertices) connected by edges. Types: directed/undirected, weighted/unweighted, cyclic/acyclic. Representations: adjacency matrix (dense), adjacency list (sparse). Algorithms: BFS (shortest path unweighted), DFS (traversal, cycle detection), Dijkstra (shortest weighted), topological sort (DAG ordering). Use for: networks, relationships, dependencies, routing. Real examples: social networks, maps, package dependencies. Time complexity depends on representation and algorithm."
    },
    {
        "question": "How do I choose between iteration and recursion?",
        "answer": "Use recursion when: problem is naturally recursive (trees, graphs), divide-and-conquer, code is clearer. Use iteration when: performance critical, deep recursion risk, simpler iteratively. Recursion issues: stack overflow, function call overhead. Optimization: tail recursion (some languages), convert to iteration with explicit stack. Many recursive solutions have elegant iterative equivalents. Dynamic programming: bottom-up iteration often faster than top-down recursion with memoization. Think recursively, implement pragmatically."
    },
    {
        "question": "What is the difference between stack and heap memory?",
        "answer": "Stack: automatic memory, function call frames, LIFO, fast allocation. Stores: local variables, return addresses. Limited size, stack overflow if exceeded. Heap: dynamic memory, manual allocation (malloc/new), slower, fragmentation possible. Stores: objects, data of unknown size at compile time. Garbage collected (Java, Python) or manual (C, C++). Stack: value types usually. Heap: reference types, large objects. Understanding helps with: performance optimization, memory bugs, language design choices."
    },
    {
        "question": "What is functional programming?",
        "answer": "FP: programming paradigm using pure functions and immutable data. Core concepts: pure functions (no side effects), immutability, first-class functions, higher-order functions, function composition. Benefits: easier reasoning, testability, parallelization. Techniques: map/filter/reduce, currying, monads (Maybe, Either). Languages: Haskell, Clojure, Erlang. Hybrid: JavaScript, Python, Scala support FP style. Use FP patterns where they simplify: data transformations, pipelines. Not dogmatic: mix with OOP as appropriate."
    },
    {
        "question": "What is object-oriented programming?",
        "answer": "OOP: paradigm organizing code around objects with state and behavior. Pillars: encapsulation (hide internals), inheritance (reuse via hierarchy), polymorphism (same interface, different implementations), abstraction (hide complexity). Benefits: models real world, code reuse, modularity. Criticisms: can lead to deep hierarchies, overengineering. Languages: Java, C#, Python, JavaScript (prototype-based). Best practices: composition over inheritance, small classes, SOLID principles. Balance: use OOP for modeling, FP for transformations."
    },
]

def main():
    """Generate general programming training examples."""
    all_examples = []
    
    # Design Patterns
    for item in DESIGN_PATTERNS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "programming",
                "subdomain": "design_patterns",
                "response_type": "concepts"
            }
        })
    
    # SOLID Principles
    for item in SOLID_PRINCIPLES:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "programming",
                "subdomain": "solid_principles",
                "response_type": "concepts"
            }
        })
    
    # Code Quality
    for item in CODE_QUALITY:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "programming",
                "subdomain": "code_quality",
                "response_type": "concepts"
            }
        })
    
    # Refactoring
    for item in REFACTORING:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "programming",
                "subdomain": "refactoring",
                "response_type": "concepts"
            }
        })
    
    # Programming Concepts
    for item in PROGRAMMING_CONCEPTS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "programming",
                "subdomain": "concepts",
                "response_type": "concepts"
            }
        })
    
    # Algorithms & Data Structures
    for item in ALGORITHMS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "programming",
                "subdomain": "algorithms",
                "response_type": "concepts"
            }
        })
    
    # Save to file
    output_file = DATA_DIR / "programming_concepts.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"  [OK] Saved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
