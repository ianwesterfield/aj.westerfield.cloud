#!/usr/bin/env python3
"""
Angular Development Training Data Generator
Target: ~250 examples for Angular framework development
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for Angular development.
You help with Angular components, services, RxJS, NgRx, and Angular best practices."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

ANGULAR_CLI_TASKS = [
    {
        "instruction": "Create new Angular project with routing and SCSS",
        "command": "ng new my-app --routing --style=scss --strict",
        "explanation": "Creates Angular project with strict mode, routing, and SCSS"
    },
    {
        "instruction": "Generate a new component",
        "command": "ng generate component features/user-profile --standalone",
        "explanation": "Creates standalone component in features folder"
    },
    {
        "instruction": "Generate a service",
        "command": "ng generate service services/user --skip-tests",
        "explanation": "Creates service without test file"
    },
    {
        "instruction": "Generate a lazy-loaded feature module",
        "command": "ng generate module features/admin --route admin --module app",
        "explanation": "Creates admin module with lazy-loaded route"
    },
    {
        "instruction": "Run Angular development server",
        "command": "ng serve --open --poll=2000",
        "explanation": "Starts dev server, opens browser, polls for changes (useful in containers)"
    },
    {
        "instruction": "Build for production",
        "command": "ng build --configuration=production",
        "explanation": "Production build with AOT, optimization, tree-shaking"
    },
    {
        "instruction": "Run unit tests with coverage",
        "command": "ng test --code-coverage --watch=false --browsers=ChromeHeadless",
        "explanation": "Runs tests once in headless browser with coverage"
    },
    {
        "instruction": "Run e2e tests",
        "command": "ng e2e",
        "explanation": "Runs end-to-end tests with configured framework"
    },
    {
        "instruction": "Update Angular to latest version",
        "command": "ng update @angular/core @angular/cli",
        "explanation": "Updates Angular core packages with migration schematics"
    },
    {
        "instruction": "Analyze bundle size",
        "command": "ng build --configuration=production --stats-json && npx webpack-bundle-analyzer dist/my-app/stats.json",
        "explanation": "Generates and visualizes bundle statistics"
    },
    {
        "instruction": "Install Angular CLI globally",
        "command": "npm install -g @angular/cli",
        "explanation": "Installs ng command globally"
    },
    {
        "instruction": "Generate a directive",
        "command": "ng generate directive directives/highlight",
        "explanation": "Creates custom directive"
    },
    {
        "instruction": "Generate a pipe",
        "command": "ng generate pipe pipes/currency-format",
        "explanation": "Creates custom pipe for transformations"
    },
    {
        "instruction": "Generate a guard",
        "command": "ng generate guard guards/auth --implements CanActivate",
        "explanation": "Creates route guard"
    },
    {
        "instruction": "Generate an interceptor",
        "command": "ng generate interceptor interceptors/auth",
        "explanation": "Creates HTTP interceptor"
    },
    {
        "instruction": "Generate a resolver",
        "command": "ng generate resolver resolvers/user",
        "explanation": "Creates route resolver for prefetching data"
    },
    {
        "instruction": "Generate an interface",
        "command": "ng generate interface models/user",
        "explanation": "Creates TypeScript interface"
    },
    {
        "instruction": "Generate an enum",
        "command": "ng generate enum models/status",
        "explanation": "Creates TypeScript enum"
    },
    {
        "instruction": "Add Angular Material",
        "command": "ng add @angular/material",
        "explanation": "Adds Material Design components"
    },
    {
        "instruction": "Add NgRx Store",
        "command": "ng add @ngrx/store@latest && ng add @ngrx/effects@latest && ng add @ngrx/store-devtools@latest",
        "explanation": "Adds NgRx state management"
    },
    {
        "instruction": "Generate NgRx feature state",
        "command": "ng generate @ngrx/schematics:feature state/user --module app.module --api",
        "explanation": "Creates NgRx reducer, actions, effects, selectors"
    },
    {
        "instruction": "Add PWA support",
        "command": "ng add @angular/pwa",
        "explanation": "Adds service worker and manifest for PWA"
    },
    {
        "instruction": "Add server-side rendering",
        "command": "ng add @angular/ssr",
        "explanation": "Adds Angular Universal for SSR"
    },
    {
        "instruction": "Lint Angular project",
        "command": "ng lint --fix",
        "explanation": "Runs ESLint and auto-fixes issues"
    },
    {
        "instruction": "Run dev server with proxy",
        "command": "ng serve --proxy-config proxy.conf.json",
        "explanation": "Proxies API calls to backend server"
    },
    {
        "instruction": "Build with specific configuration",
        "command": "ng build --configuration=staging",
        "explanation": "Uses staging environment configuration"
    },
    {
        "instruction": "Generate library",
        "command": "ng generate library my-lib",
        "explanation": "Creates publishable Angular library"
    },
    {
        "instruction": "Build library",
        "command": "ng build my-lib --configuration=production",
        "explanation": "Builds library for npm publishing"
    },
    {
        "instruction": "Run specific tests",
        "command": "ng test --include='**/user.service.spec.ts'",
        "explanation": "Runs tests matching pattern"
    },
    {
        "instruction": "Generate class",
        "command": "ng generate class models/user --type=model",
        "explanation": "Creates TypeScript class file"
    },
    {
        "instruction": "Check Angular version",
        "command": "ng version",
        "explanation": "Shows Angular CLI and packages versions"
    },
    {
        "instruction": "Show available schematics",
        "command": "ng generate --help",
        "explanation": "Lists all available generators"
    },
    {
        "instruction": "Add Tailwind CSS",
        "command": "npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init",
        "explanation": "Sets up Tailwind with Angular"
    },
    {
        "instruction": "Run with SSL",
        "command": "ng serve --ssl --ssl-cert ./ssl/cert.pem --ssl-key ./ssl/key.pem",
        "explanation": "Runs dev server with HTTPS"
    },
    {
        "instruction": "Extract i18n messages",
        "command": "ng extract-i18n --output-path src/locale",
        "explanation": "Extracts translation messages for i18n"
    },
    {
        "instruction": "Build with specific base href",
        "command": "ng build --base-href /myapp/",
        "explanation": "Sets base href for deployment to subdirectory"
    },
    {
        "instruction": "Cache Angular build",
        "command": "ng config cli.cache.enabled true",
        "explanation": "Enables persistent build cache"
    },
    {
        "instruction": "Clear Angular cache",
        "command": "ng cache clean",
        "explanation": "Clears the Angular CLI cache"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Create Angular standalone component with signals",
        "language": "typescript",
        "code": """import { Component, signal, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { UserService } from '../services/user.service';

interface User {
  id: number;
  name: string;
  email: string;
}

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="user-list">
      <input 
        [(ngModel)]="searchTerm" 
        placeholder="Search users..."
        (ngModelChange)="onSearchChange($event)"
      />
      
      @if (loading()) {
        <div class="loading">Loading...</div>
      }
      
      @if (error()) {
        <div class="error">{{ error() }}</div>
      }
      
      <ul>
        @for (user of filteredUsers(); track user.id) {
          <li (click)="selectUser(user)">
            {{ user.name }} - {{ user.email }}
          </li>
        } @empty {
          <li>No users found</li>
        }
      </ul>
      
      @if (selectedUser()) {
        <div class="selected">
          Selected: {{ selectedUser()?.name }}
        </div>
      }
      
      <p>Total: {{ userCount() }} users</p>
    </div>
  `,
  styles: [`
    .user-list { padding: 1rem; }
    .loading { color: blue; }
    .error { color: red; }
    .selected { background: #e0e0e0; padding: 0.5rem; }
  `]
})
export class UserListComponent {
  private userService = inject(UserService);
  
  // Signals for reactive state
  users = signal<User[]>([]);
  loading = signal(false);
  error = signal<string | null>(null);
  searchTerm = '';
  selectedUser = signal<User | null>(null);
  
  // Computed values
  filteredUsers = computed(() => {
    const term = this.searchTerm.toLowerCase();
    return this.users().filter(u => 
      u.name.toLowerCase().includes(term) ||
      u.email.toLowerCase().includes(term)
    );
  });
  
  userCount = computed(() => this.filteredUsers().length);
  
  constructor() {
    // Effect runs when dependencies change
    effect(() => {
      console.log('User count changed:', this.userCount());
    });
    
    this.loadUsers();
  }
  
  async loadUsers() {
    this.loading.set(true);
    this.error.set(null);
    
    try {
      const users = await this.userService.getUsers();
      this.users.set(users);
    } catch (e) {
      this.error.set('Failed to load users');
    } finally {
      this.loading.set(false);
    }
  }
  
  selectUser(user: User) {
    this.selectedUser.set(user);
  }
  
  onSearchChange(term: string) {
    // searchTerm is already updated via ngModel
    // This is for any additional logic
  }
}""",
        "explanation": "Modern Angular 17+ with signals, new control flow syntax, standalone"
    },
    {
        "instruction": "Create Angular service with RxJS",
        "language": "typescript",
        "code": """import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { 
  catchError, 
  retry, 
  map, 
  tap, 
  shareReplay,
  switchMap,
  debounceTime,
  distinctUntilChanged 
} from 'rxjs/operators';
import { environment } from '../environments/environment';

export interface User {
  id: number;
  name: string;
  email: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl + '/users';
  
  // Cached observable with shareReplay
  private users$ = this.http.get<User[]>(this.baseUrl).pipe(
    retry(2),
    catchError(this.handleError),
    shareReplay({ bufferSize: 1, refCount: true })
  );
  
  // State management with BehaviorSubject
  private selectedUserSubject = new BehaviorSubject<User | null>(null);
  selectedUser$ = this.selectedUserSubject.asObservable();
  
  getUsers(): Observable<User[]> {
    return this.users$;
  }
  
  getUserById(id: number): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/${id}`).pipe(
      catchError(this.handleError)
    );
  }
  
  // Search with debounce
  searchUsers(term$: Observable<string>): Observable<User[]> {
    return term$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(term => {
        if (!term.trim()) {
          return of([]);
        }
        return this.http.get<User[]>(`${this.baseUrl}?search=${term}`);
      }),
      catchError(() => of([]))
    );
  }
  
  createUser(user: Omit<User, 'id'>): Observable<User> {
    return this.http.post<User>(this.baseUrl, user).pipe(
      tap(newUser => {
        // Invalidate cache by reassigning
        this.invalidateCache();
      }),
      catchError(this.handleError)
    );
  }
  
  updateUser(id: number, updates: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.baseUrl}/${id}`, updates).pipe(
      tap(() => this.invalidateCache()),
      catchError(this.handleError)
    );
  }
  
  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`).pipe(
      tap(() => this.invalidateCache()),
      catchError(this.handleError)
    );
  }
  
  selectUser(user: User | null) {
    this.selectedUserSubject.next(user);
  }
  
  private invalidateCache() {
    // Force cache refresh on next subscription
    this.users$ = this.http.get<User[]>(this.baseUrl).pipe(
      retry(2),
      catchError(this.handleError),
      shareReplay({ bufferSize: 1, refCount: true })
    );
  }
  
  private handleError(error: HttpErrorResponse) {
    let message = 'An error occurred';
    
    if (error.error instanceof ErrorEvent) {
      message = error.error.message;
    } else {
      message = `Error ${error.status}: ${error.message}`;
    }
    
    console.error('UserService error:', message);
    return throwError(() => new Error(message));
  }
}""",
        "explanation": "Service with caching, RxJS operators, error handling, state management"
    },
    {
        "instruction": "Implement route guards and resolvers",
        "language": "typescript",
        "code": """import { Injectable, inject } from '@angular/core';
import { 
  CanActivate, 
  CanActivateFn,
  Router, 
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  ResolveFn
} from '@angular/router';
import { AuthService } from './auth.service';
import { UserService, User } from './user.service';
import { Observable, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';

// Functional guard (preferred in Angular 14+)
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  if (authService.isAuthenticated()) {
    return true;
  }
  
  // Store attempted URL for redirect after login
  authService.redirectUrl = state.url;
  router.navigate(['/login']);
  return false;
};

// Role-based guard
export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  const requiredRoles = route.data['roles'] as string[];
  const userRoles = authService.currentUser?.roles || [];
  
  const hasRole = requiredRoles.some(role => userRoles.includes(role));
  
  if (!hasRole) {
    router.navigate(['/unauthorized']);
    return false;
  }
  
  return true;
};

// Resolver - loads data before route activation
export const userResolver: ResolveFn<User | null> = (route) => {
  const userService = inject(UserService);
  const router = inject(Router);
  const id = Number(route.paramMap.get('id'));
  
  return userService.getUserById(id).pipe(
    catchError(error => {
      console.error('Error loading user:', error);
      router.navigate(['/users']);
      return of(null);
    })
  );
};

// Route configuration
export const routes = [
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard.component'),
    canActivate: [authGuard]
  },
  {
    path: 'admin',
    loadComponent: () => import('./admin/admin.component'),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['admin'] }
  },
  {
    path: 'users/:id',
    loadComponent: () => import('./user-detail/user-detail.component'),
    canActivate: [authGuard],
    resolve: { user: userResolver }
  },
  {
    path: 'users/:id/edit',
    loadComponent: () => import('./user-edit/user-edit.component'),
    canActivate: [authGuard],
    canDeactivate: [unsavedChangesGuard]  // Prevent leaving with unsaved changes
  }
];

// Unsaved changes guard
export const unsavedChangesGuard: CanActivateFn = (route, state) => {
  const component = route.component as any;
  
  if (component?.hasUnsavedChanges?.()) {
    return window.confirm('You have unsaved changes. Leave anyway?');
  }
  
  return true;
};""",
        "explanation": "Functional guards, role-based access, resolvers, route config"
    },
    {
        "instruction": "Create reactive form with validation",
        "language": "typescript",
        "code": """import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  ReactiveFormsModule, 
  FormBuilder, 
  FormGroup, 
  Validators,
  AbstractControl,
  ValidationErrors,
  AsyncValidatorFn
} from '@angular/forms';
import { UserService } from '../services/user.service';
import { debounceTime, map, catchError, first } from 'rxjs/operators';
import { of } from 'rxjs';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <div class="form-group">
        <label for="name">Name</label>
        <input id="name" formControlName="name" />
        @if (form.get('name')?.errors?.['required'] && form.get('name')?.touched) {
          <span class="error">Name is required</span>
        }
        @if (form.get('name')?.errors?.['minlength']) {
          <span class="error">Name must be at least 2 characters</span>
        }
      </div>
      
      <div class="form-group">
        <label for="email">Email</label>
        <input id="email" formControlName="email" type="email" />
        @if (form.get('email')?.errors?.['required'] && form.get('email')?.touched) {
          <span class="error">Email is required</span>
        }
        @if (form.get('email')?.errors?.['email']) {
          <span class="error">Invalid email format</span>
        }
        @if (form.get('email')?.errors?.['emailTaken']) {
          <span class="error">Email already in use</span>
        }
        @if (form.get('email')?.pending) {
          <span class="info">Checking availability...</span>
        }
      </div>
      
      <div formGroupName="address">
        <h4>Address</h4>
        <input formControlName="street" placeholder="Street" />
        <input formControlName="city" placeholder="City" />
        <input formControlName="zip" placeholder="ZIP" />
        @if (form.get('address')?.errors?.['zipCityMismatch']) {
          <span class="error">ZIP code doesn't match city</span>
        }
      </div>
      
      <div class="form-group">
        <label for="password">Password</label>
        <input id="password" formControlName="password" type="password" />
      </div>
      
      <div class="form-group">
        <label for="confirmPassword">Confirm Password</label>
        <input id="confirmPassword" formControlName="confirmPassword" type="password" />
        @if (form.errors?.['passwordMismatch']) {
          <span class="error">Passwords don't match</span>
        }
      </div>
      
      <button type="submit" [disabled]="form.invalid || form.pending">
        Submit
      </button>
    </form>
  `
})
export class UserFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  
  form!: FormGroup;
  
  ngOnInit() {
    this.form = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', 
        [Validators.required, Validators.email],
        [this.emailExistsValidator()]  // Async validator
      ],
      address: this.fb.group({
        street: [''],
        city: ['', Validators.required],
        zip: ['', [Validators.required, Validators.pattern(/^\\d{5}$/)]]
      }, { validators: this.zipCityValidator }),
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });
  }
  
  // Cross-field validator
  passwordMatchValidator(group: AbstractControl): ValidationErrors | null {
    const password = group.get('password')?.value;
    const confirm = group.get('confirmPassword')?.value;
    return password === confirm ? null : { passwordMismatch: true };
  }
  
  // Nested group validator
  zipCityValidator(group: AbstractControl): ValidationErrors | null {
    const city = group.get('city')?.value;
    const zip = group.get('zip')?.value;
    // Add real validation logic
    return null;
  }
  
  // Async validator - checks server
  emailExistsValidator(): AsyncValidatorFn {
    return (control: AbstractControl) => {
      return this.userService.checkEmailExists(control.value).pipe(
        debounceTime(300),
        map(exists => exists ? { emailTaken: true } : null),
        catchError(() => of(null)),
        first()
      );
    };
  }
  
  onSubmit() {
    if (this.form.valid) {
      console.log('Form data:', this.form.value);
      // Submit to service
    } else {
      // Mark all as touched to show errors
      this.form.markAllAsTouched();
    }
  }
}""",
        "explanation": "Reactive forms with sync/async validators, nested groups, cross-field validation"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up Angular project with NgRx state management",
        "steps": [
            "Create project: ng new app --standalone --routing --style=scss",
            "Install NgRx: ng add @ngrx/store @ngrx/effects @ngrx/store-devtools",
            "Create feature state folder: src/app/store/",
            "Define state interface for each feature",
            "Create actions with createActionGroup()",
            "Create reducer with createReducer()",
            "Create selectors with createFeatureSelector/createSelector",
            "Create effects for async operations",
            "Register store in app.config.ts with provideStore()",
            "Register effects with provideEffects()",
            "Add StoreDevtoolsModule for debugging",
            "Create facade service to encapsulate store access",
            "Connect components to store via selectors",
            "Test reducers and selectors with unit tests"
        ]
    },
    {
        "instruction": "Implement lazy loading and performance optimization",
        "steps": [
            "Identify feature modules for lazy loading",
            "Use loadComponent() in routes for standalone components",
            "Use loadChildren() for feature modules",
            "Implement route preloading strategy",
            "Add OnPush change detection to components",
            "Use trackBy in *ngFor / @for",
            "Implement virtual scrolling for long lists",
            "Use async pipe instead of manual subscriptions",
            "Add bundle analyzer to identify large modules",
            "Configure lazy loading for images",
            "Set up service worker for caching",
            "Use web workers for heavy computations",
            "Profile with Angular DevTools",
            "Monitor Core Web Vitals"
        ]
    },
    {
        "instruction": "Add authentication to Angular application",
        "steps": [
            "Create AuthService for login/logout/token management",
            "Store tokens securely (httpOnly cookies preferred, or memory)",
            "Create HTTP interceptor for adding auth headers",
            "Create HTTP interceptor for handling 401 responses",
            "Implement auth guard for protected routes",
            "Create login/register components",
            "Add loading state during auth operations",
            "Implement token refresh flow",
            "Create user state/store for current user",
            "Add role-based access control",
            "Handle auth state persistence across refreshes",
            "Implement logout on all tabs (BroadcastChannel)",
            "Add CSRF protection if using cookies",
            "Test auth flow end-to-end"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What are Angular signals and why use them?",
        "answer": "Signals are Angular 16+ reactive primitives for fine-grained reactivity. signal() creates reactive value, computed() derives values, effect() runs side effects. Benefits over RxJS: simpler API for sync state, automatic dependency tracking, better performance (zone-less possible). Use signals for: component state, simple derived values. Use RxJS for: async operations, complex streams, HTTP. Signals work with change detection for surgical updates. Interop: toSignal(), toObservable() for conversion."
    },
    {
        "question": "What is the difference between standalone and NgModule components?",
        "answer": "NgModules: traditional Angular - components declared in module, share dependencies via imports. Standalone: Angular 14+ - components self-contained, import dependencies directly, no module needed. Benefits: simpler, tree-shakeable, easier lazy loading. Declare with standalone: true in @Component. Import other standalone components/directives directly. New projects should use standalone. Can mix: standalone components work in NgModule apps. Migration path available."
    },
    {
        "question": "How does dependency injection work in Angular?",
        "answer": "DI is built into Angular. Services decorated with @Injectable(). providedIn: 'root' = singleton app-wide. Provide in component = new instance per component. Injector hierarchy: platform → root → component tree. inject() function or constructor injection. Use InjectionToken for non-class values. useClass/useValue/useFactory for custom providers. Benefits: testability (mock services), loose coupling, configuration flexibility. Avoid circular dependencies."
    },
    {
        "question": "What is RxJS and how is it used in Angular?",
        "answer": "RxJS = Reactive Extensions for JavaScript. Handles async data streams. Core: Observable (stream of values), Observer (subscriber), Operators (transform data). Angular uses for: HTTP responses, form value changes, router events, state management. Common operators: map, filter, switchMap, mergeMap, catchError, tap, debounceTime. Always unsubscribe to prevent memory leaks - use async pipe, takeUntilDestroyed(), or manual unsubscribe in ngOnDestroy. Subject family for multicasting."
    },
    {
        "question": "What are Angular components and templates?",
        "answer": "Components are building blocks of Angular UI. @Component decorator defines: selector (HTML tag), template/templateUrl (view), styleUrls (CSS). Templates use Angular syntax: {{interpolation}}, [property] binding, (event) binding, [(two-way)]. Input/Output for parent-child communication. @Input() receives data, @Output() emits events via EventEmitter. Component lifecycle: ngOnInit, ngOnChanges, ngAfterViewInit, ngOnDestroy. Keep components focused - single responsibility."
    },
    {
        "question": "How does Angular routing work?",
        "answer": "RouterModule configures navigation. Routes array maps paths to components. RouterOutlet displays routed components. routerLink for navigation, routerLinkActive for styling. Route params: /user/:id accessed via ActivatedRoute. Query params: ?key=value. Guards protect routes: CanActivate, CanDeactivate, Resolve. Lazy loading with loadChildren/loadComponent. Child routes for nested views. Router events for tracking navigation. Navigate programmatically with Router.navigate()."
    },
    {
        "question": "What are Angular pipes?",
        "answer": "Pipes transform data in templates. Built-in: date, currency, uppercase, lowercase, json, async. Use: {{ value | pipeName:arg1:arg2 }}. async pipe subscribes to Observable/Promise, auto-unsubscribes. Pure pipes (default): only recalculate when input reference changes. Impure pipes: recalculate every change detection. Create custom: @Pipe decorator, implement PipeTransform. Standalone pipes: standalone: true. Chain pipes: {{ value | pipe1 | pipe2 }}. Keep pipes simple - complex logic belongs in services."
    },
    {
        "question": "What are Angular directives?",
        "answer": "Directives extend HTML. Types: Components (with template), Structural (*ngIf, *ngFor - change DOM), Attribute (ngClass, ngStyle - change appearance). Create custom: @Directive decorator. Access host element with ElementRef. Renderer2 for safe DOM manipulation. HostBinding/HostListener for property/event binding. @Input on directive for configuration. Structural directives use * syntax (sugar for ng-template). Built-in new control flow (@if, @for) replacing structural directives in Angular 17+."
    },
    {
        "question": "What is Angular HttpClient?",
        "answer": "HttpClient makes HTTP requests, returns Observables. Import HttpClientModule or provideHttpClient(). Methods: get(), post(), put(), delete(), patch(). Type responses: http.get<User[]>(url). Headers with HttpHeaders. Request options: params, headers, reportProgress. Interceptors modify requests/responses globally: logging, auth tokens, error handling. Handle errors with catchError operator. RxJS operators for retry, timeout, caching. Subscribe or use async pipe."
    },
    {
        "question": "How do Angular forms work?",
        "answer": "Two approaches: Template-driven (FormsModule) and Reactive (ReactiveFormsModule). Template-driven: ngModel binds values, simple validation. Reactive: FormGroup/FormControl in component, more control, easier testing. Validators: required, minLength, pattern, custom. Access validation: form.get('field')?.errors. Touched/dirty/pristine states for UX. FormArray for dynamic fields. valueChanges Observable for reactions. Use reactive for complex forms, template-driven for simple."
    },
    {
        "question": "What is Angular CLI?",
        "answer": "CLI is command-line tool for Angular development. ng new creates projects. ng generate (g) scaffolds: components, services, modules, pipes, directives, guards. ng serve runs dev server with live reload. ng build compiles for production. ng test runs unit tests with Karma. ng e2e runs end-to-end tests. ng add installs libraries with schematics. ng update upgrades packages. Configurations in angular.json. Schematics automate code generation."
    },
    {
        "question": "What is the async pipe?",
        "answer": "Async pipe subscribes to Observable/Promise in template. {{ observable$ | async }}. Key benefit: auto-unsubscribes on component destroy - no memory leaks. Use with *ngIf: *ngIf='data$ | async as data'. Multiple subscriptions: each use creates new subscription. Store in variable to avoid multiple subscribes: *ngIf='obs$ | async as value'. With signals: not needed, signals work directly in templates. Prefer async pipe over manual subscriptions for cleaner code."
    },
    {
        "question": "What are Angular environments?",
        "answer": "Environments configure app for different deployments. Files in src/environments/: environment.ts (dev), environment.prod.ts (production). Access: import { environment } from '../environments/environment'. Build replaces files: ng build --configuration=production. Define: API URLs, feature flags, logging levels. Configure in angular.json fileReplacements. Create custom: environment.staging.ts. Keep secrets out - use backend or runtime config for sensitive values."
    },
    {
        "question": "What are ViewChild and ContentChild?",
        "answer": "@ViewChild queries elements in component's template. @ContentChild queries projected content (ng-content). Access after view initialized (ngAfterViewInit). Query by: component type, directive, template reference (#ref). Static: true for access in ngOnInit (no structural directives). @ViewChildren/@ContentChildren return QueryList for multiple matches. QueryList has changes Observable. Use to access child component methods or native elements."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What are Angular control flow blocks (@if, @for)?",
        "answer": "Angular 17+ introduced built-in control flow replacing *ngIf/*ngFor. @if (condition) { } @else if { } @else { }. @for (item of items; track item.id) { } @empty { }. @switch (value) { @case (x) { } @default { } }. Benefits: no imports needed, better performance, cleaner syntax, required track expression prevents bugs. Migration: ng generate @angular/core:control-flow. Works in templates, replaces structural directives for common cases."
    },
    {
        "question": "How do you optimize Angular change detection?",
        "answer": "Default: checks entire component tree on any event. OnPush: only checks when @Input references change, events from component, async pipe emits, or manual markForCheck(). Use OnPush everywhere possible. With signals: even more granular - only affected template parts update. Avoid: complex computations in templates (use computed/pipes), unnecessary object recreation. Tools: Angular DevTools profiler shows change detection cycles. Zone-less apps with signals = maximum performance."
    },
    {
        "question": "What is NgRx and when should I use it?",
        "answer": "NgRx is Redux-inspired state management for Angular. Core: Store (state container), Actions (state change events), Reducers (pure functions updating state), Selectors (query state), Effects (side effects). Use when: complex state shared across features, need time-travel debugging, team benefits from strict patterns. Don't use for: simple apps, local component state. Alternatives: signals for simple state, component stores for feature state. Learning curve is real - evaluate if complexity is justified."
    },
    {
        "question": "How do you test Angular components?",
        "answer": "TestBed configures testing module. ComponentFixture gives access to component instance and DOM. Types: isolated (no TestBed, test class only), shallow (mock children), integration (real children). Use fakeAsync/tick for async. Mock services with jasmine spies or jest mocks. Query DOM with fixture.debugElement.query(By.css()). Trigger events with triggerEventHandler() or native events. Test observables with done callback or async/await. For forms: set values and check validity. Prefer testing behavior over implementation."
    },
    {
        "question": "What are Angular interceptors?",
        "answer": "Interceptors modify HTTP requests/responses globally. Implement HttpInterceptor interface. Common uses: add auth tokens, log requests, handle errors, show loading, cache responses. Chain multiple interceptors - order matters. Provide with HTTP_INTERCEPTORS token or withInterceptors() for functional style. Access request/response via HttpRequest/HttpResponse. Clone request to modify (immutable). next.handle() passes to next interceptor. Use withInterceptorsFromDi() for functional interceptors."
    },
    {
        "question": "What is lazy loading in Angular?",
        "answer": "Lazy loading loads modules on demand, reducing initial bundle. Routes: loadChildren for NgModules, loadComponent for standalone. Syntax: loadChildren: () => import('./feature/feature.module').then(m => m.FeatureModule). Preloading strategies: PreloadAllModules, custom strategies. Check bundle sizes with ng build --stats-json + webpack-bundle-analyzer. Lazy load below-fold content. Code splitting automatic with dynamic imports. Guard lazy routes appropriately."
    },
    {
        "question": "What is Angular SSR (Server-Side Rendering)?",
        "answer": "SSR renders Angular on server for initial HTML. Benefits: SEO, faster perceived load, social media previews. Angular Universal/SSR: ng add @angular/ssr. Hydration: client takes over server HTML without re-render. isPlatformBrowser/isPlatformServer for platform-specific code. Transfer State prevents duplicate API calls. Avoid direct DOM access - use Renderer2, DOCUMENT token. Build: ng build && ng run app:server. Deploy: Node.js server or serverless. Consider: caching, CDN, static site generation."
    },
    {
        "question": "How do you implement authentication in Angular?",
        "answer": "Store tokens in memory or secure storage (not localStorage for sensitive apps). HTTP interceptor adds Authorization header. Auth guard protects routes (CanActivate, CanActivateChild). Login: call API, store token, redirect. Logout: clear token, redirect to login. Token refresh: interceptor catches 401, refreshes, retries. Role-based access: check user roles in guards/templates. OAuth/OIDC: use angular-oauth2-oidc library. Consider: XSS protection, token expiry, secure transmission."
    },
    {
        "question": "What are Angular animations?",
        "answer": "@angular/animations module. Define in component metadata: animations: [trigger('name', [])]. States: define named states with style(). Transitions: specify state changes with animate(). trigger, state, style, animate, transition. void state for enter/leave. :enter/:leave aliases. Query for child elements. Stagger for sequential animations. AnimationBuilder for programmatic control. DisableAnimations for testing. Performance: use transform/opacity, will-change, avoid layout triggers."
    },
    {
        "question": "What is content projection (ng-content)?",
        "answer": "Content projection passes content from parent to child component. <ng-content> marks insertion point. Select content with selectors: <ng-content select='[header]'>. Multiple slots: different selectors. Default slot: ng-content without selector. ngProjectAs for dynamic projection. Content children accessible via @ContentChild/@ContentChildren. Use for: wrapper components, card layouts, modal content, customizable components. Alternative: ng-template with structural directive for more control."
    },
    {
        "question": "How do you handle errors globally in Angular?",
        "answer": "ErrorHandler class catches all uncaught errors. Extend and provide custom handler. HTTP errors: interceptor catches, transforms, handles globally. Show user-friendly messages. Log to external service (Sentry, AppInsights). Error boundaries pattern: catch errors in specific components. RxJS catchError for observable chains. Don't swallow errors - log even if handled. Different handling for dev vs prod. Consider retry logic for transient failures."
    },
    {
        "question": "What are Angular schematics?",
        "answer": "Schematics are code generators and transformers. CLI uses schematics for ng generate. Library schematics for ng add setup. Create custom: ng generate library my-schematics. Schematics collection.json defines available schematics. Tree represents virtual filesystem. Rule transforms tree. Template files with variable substitution. Chaining rules for complex operations. Use for: consistent code generation, migrations, library setup. Test schematics with SchematicTestRunner."
    },
    {
        "question": "What is Zone.js and how does it relate to change detection?",
        "answer": "Zone.js patches async APIs (setTimeout, Promise, events) to notify Angular. Angular runs change detection after zone operations complete. NgZone service: run() executes in zone, runOutsideAngular() bypasses zone. Use runOutsideAngular for performance-critical code that shouldn't trigger CD. Zone-less Angular: possible with signals, provideExperimentalZonelessChangeDetection(). Debugging: enableProdMode() hides some zone errors. Zone.js increases bundle size, zone-less is the future."
    },
    {
        "question": "How do you implement real-time features in Angular?",
        "answer": "WebSocket: native WebSocket or socket.io-client. RxJS WebSocketSubject simplifies: webSocket(url). SSE: EventSource API wrapped in Observable. Polling: interval() + switchMap. Firebase: @angular/fire with real-time listeners. SignalR: @microsoft/signalr. Handle: reconnection, message queuing, state sync. OnPush + signals for efficient updates. Unsubscribe on destroy. Consider: connection state UI, offline handling, optimistic updates."
    },
    # === EXPANDED ADVANCED CONCEPTS ===
    {
        "question": "What are deferrable views in Angular?",
        "answer": "@defer blocks (Angular 17+) lazy load template sections. Syntax: @defer (on viewport) { <heavy-component /> } @placeholder { Loading... }. Triggers: on viewport, on idle, on timer, on hover, on interaction. Built-in blocks: @loading, @error, @placeholder. Prefetching with prefetch. Reduces initial bundle by deferring non-critical UI. Automatic code splitting. Works with any component, no special setup needed. Great for below-fold content, modals, heavy visualizations."
    },
    {
        "question": "How do you create a custom structural directive?",
        "answer": "Structural directives manipulate DOM. Steps: 1) @Directive with selector '[myDirective]'. 2) Inject TemplateRef and ViewContainerRef. 3) Use viewContainer.createEmbeddedView(template) to render. 4) Use viewContainer.clear() to remove. Example: *myIf='condition' creates/destroys template. Context object passes data to template: let-item='$implicit'. Microsyntax: *dir='exp; let x' expands to <ng-template [dir]='exp' let-x>. Test with By.directive()."
    },
    {
        "question": "What is the inject() function in Angular?",
        "answer": "inject() is functional alternative to constructor injection. Use in: constructors, field initializers, factory functions. inject(ServiceClass) returns instance. Benefits: cleaner syntax, works in functions, enables composition. Can use in route guards, interceptors, resolvers. Options: { optional: true } for optional deps. Must be called in injection context (component creation, factory). Prefer for: simple injections, functional patterns. Constructor for: complex initialization logic."
    },
    {
        "question": "How do you implement micro-frontends with Angular?",
        "answer": "Approaches: 1) Module Federation (Webpack 5) - share dependencies, independent deployment. 2) Web Components - Angular Elements wraps components as custom elements. 3) iframes - isolation but communication complexity. Module Federation: @angular-architects/module-federation. Define exposed/consumed modules. Share common deps to avoid duplication. Routing: federated routes load remote modules. Challenges: styling conflicts, state sharing, version alignment. Consider: monorepo for simpler alternative."
    },
    {
        "question": "What is the ResolveFn and how does it work?",
        "answer": "ResolveFn pre-fetches data before route activates. Functional resolver: export const userResolver: ResolveFn<User> = (route) => inject(UserService).getUser(route.params['id']). Route config: resolve: { user: userResolver }. Access in component: route.snapshot.data['user']. Benefits: component receives ready data, loading handled by router. Options: return Observable, Promise, or sync value. Error handling: catchError in resolver or route errorElement. Consider: showing loading state during resolve."
    },
    {
        "question": "How do you implement dynamic components in Angular?",
        "answer": "ViewContainerRef.createComponent() instantiates components dynamically. Get container: @ViewChild('container', { read: ViewContainerRef }). Create: container.createComponent(MyComponent). Pass inputs: componentRef.setInput('data', value). Access instance: componentRef.instance. Destroy: componentRef.destroy() or container.clear(). Angular 13+: no ComponentFactoryResolver needed. Use for: modals, tabs, dynamic forms, plugin systems. NgComponentOutlet directive for template-based dynamic loading."
    },
    {
        "question": "What are Angular Elements?",
        "answer": "Angular Elements packages components as Web Components (custom elements). Use: createCustomElement() + customElements.define(). Benefits: use Angular components in non-Angular apps, micro-frontends, CMS integration. Build: special build config outputs standalone bundle. Inputs become attributes, outputs become custom events. Polyfill for older browsers: @webcomponents/webcomponentsjs. Considerations: bundle size includes Angular runtime, styling encapsulation. Good for: widget distribution, gradual migration."
    },
    {
        "question": "How do you optimize bundle size in Angular?",
        "answer": "Analysis: ng build --stats-json + webpack-bundle-analyzer. Techniques: lazy loading routes, tree shaking (avoid barrel exports), standalone components (better tree shaking), defer loading. Remove unused: imports, polyfills, third-party features. Compression: enable gzip/brotli on server. Images: lazy load, use modern formats. Consider: CDN for common libs, code splitting. Angular CLI handles most optimization in prod build. Check: moment.js → date-fns, lodash → lodash-es."
    },
    {
        "question": "What is the Component Store pattern?",
        "answer": "ComponentStore (@ngrx/component-store) is lightweight reactive state for components/features. Simpler than full NgRx Store. Core: select$ (read state), updater (sync updates), effect (async operations). Create: extend ComponentStore<State>. Local state: provide in component, destroyed with component. Shared state: provide in module/root. Benefits: reactive, testable, less boilerplate than NgRx Store. Use for: feature-level state, complex component state. Migrate to Store if needs grow."
    },
    {
        "question": "How do you implement input transforms in Angular?",
        "answer": "Input transforms (Angular 16+) convert input values. Syntax: @Input({ transform: booleanAttribute }) disabled = false. Built-in: booleanAttribute (string → boolean), numberAttribute (string → number). Custom: @Input({ transform: (v: string) => v.toUpperCase() }). Use for: attribute conversion, normalization, validation. Works with template and programmatic inputs. Reduces boilerplate from ngOnChanges parsing. Combine with required: @Input({ required: true })."
    },
    {
        "question": "What is the Router's withComponentInputBinding feature?",
        "answer": "withComponentInputBinding() (Angular 16+) binds route data directly to component inputs. Enable: provideRouter(routes, withComponentInputBinding()). Route params become @Input(): @Input() id!: string. Query params: @Input() search?: string. Route data: @Input() title!: string. Resolve data: @Input() user!: User. Benefits: cleaner code, no ActivatedRoute injection for simple cases. Type-safe with proper input typing. Still use ActivatedRoute for complex scenarios."
    },
    {
        "question": "How do you handle complex forms with FormArray?",
        "answer": "FormArray holds dynamic list of FormControls/FormGroups. Create: new FormArray([new FormControl()]). Add: array.push(control). Remove: array.removeAt(index). Iterate: *ngFor='let control of array.controls; index as i'. FormBuilder: fb.array([]). Nested FormGroups in array for complex items. Validation: array-level validators. Dynamic adding: addItem() { this.items.push(fb.group({...})) }. Clear: array.clear(). Access: array.at(index) or controls[index]."
    },
    {
        "question": "What are output transforms (model/signal outputs)?",
        "answer": "Angular 17.1+ model() creates two-way bindable signal. @Input() + @Output() combined: name = model<string>(''). Use: [(name)]='parentSignal'. Signal-based outputs: output() function. output<T>() creates OutputEmitterRef. Emit: this.saved.emit(value). Benefits: type-safe, signal-based reactivity. model() enables two-way binding with signals. Simpler than traditional @Input/@Output pairs. Migrating: replace EventEmitter patterns gradually."
    },
]

# =============================================================================
# ERROR SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "ExpressionChangedAfterItHasBeenCheckedError",
        "error_type": "change_detection",
        "response": {
            "status": "common_error",
            "cause": "Value changed between change detection check and view render",
            "common_triggers": [
                "Modifying state in ngAfterViewInit",
                "Async operation completing during CD cycle",
                "Parent changing child input during CD"
            ],
            "solutions": [
                "Move logic to ngOnInit if possible",
                "Use setTimeout(() => { ... }) to defer",
                "ChangeDetectorRef.detectChanges() after change",
                "Restructure to avoid change during CD"
            ],
            "note": "Only appears in dev mode - helps catch bugs"
        }
    },
    {
        "instruction": "Can't bind to 'ngModel' since it isn't a known property",
        "error_type": "module_import",
        "response": {
            "status": "missing_import",
            "cause": "FormsModule not imported",
            "solutions": [
                "Standalone component: add FormsModule to imports array",
                "NgModule: add FormsModule to module imports",
                "For reactive forms: use ReactiveFormsModule instead"
            ],
            "code": "imports: [CommonModule, FormsModule]"
        }
    },
    {
        "instruction": "Memory leak from Observable subscription",
        "error_type": "resource_leak",
        "response": {
            "status": "best_practice_violation",
            "cause": "Subscription not cleaned up when component destroyed",
            "solutions": [
                "Use async pipe in template (auto-unsubscribes)",
                "takeUntilDestroyed() in injection context",
                "Subject + takeUntil pattern",
                "Store subscription and unsubscribe in ngOnDestroy"
            ],
            "recommended": "async pipe or takeUntilDestroyed() for cleanest code",
            "code_example": "this.http.get(url).pipe(takeUntilDestroyed()).subscribe()"
        }
    },
    {
        "instruction": "NullInjectorError: No provider for Service",
        "error_type": "dependency_injection",
        "response": {
            "status": "missing_provider",
            "cause": "Service not provided in DI system",
            "solutions": [
                "Add @Injectable({ providedIn: 'root' }) to service",
                "Provide in component: providers: [MyService]",
                "Provide in module: providers array",
                "For standalone: importProvidersFrom() or direct providers"
            ],
            "check": "Verify service file exists and is exported correctly"
        }
    },
    {
        "instruction": "NG0100: Expression has changed after it was checked",
        "error_type": "change_detection",
        "response": {
            "status": "development_warning",
            "cause": "Template binding changed during change detection",
            "common_causes": [
                "Getters that return new objects",
                "Calling methods in template that return new values",
                "Service updating data during CD cycle"
            ],
            "solutions": [
                "Cache computed values in component property",
                "Use signals or computed for derived values",
                "Avoid calling methods in template for complex logic",
                "Use OnPush change detection"
            ]
        }
    },
    {
        "instruction": "Can't bind to 'formGroup' since it isn't a known property",
        "error_type": "module_import",
        "response": {
            "status": "missing_import",
            "cause": "ReactiveFormsModule not imported",
            "solutions": [
                "Standalone: imports: [ReactiveFormsModule]",
                "NgModule: add ReactiveFormsModule to imports",
                "Verify FormGroup is imported from @angular/forms"
            ],
            "note": "FormGroup, FormControl, Validators are from @angular/forms"
        }
    },
    {
        "instruction": "Error: Cannot find module",
        "error_type": "build_error",
        "response": {
            "status": "module_resolution",
            "checks": [
                "Verify package is installed: npm list <package>",
                "Check import path is correct",
                "Clear node_modules and reinstall: rm -rf node_modules && npm install",
                "Check tsconfig.json paths configuration",
                "Restart ng serve after installing packages"
            ],
            "common_causes": [
                "Typo in import path",
                "Package not installed",
                "Wrong package name",
                "Missing @types package for TypeScript"
            ]
        }
    },
    {
        "instruction": "Template parse errors: No directive found with exportAs",
        "error_type": "template_error",
        "response": {
            "status": "directive_not_available",
            "cause": "#ref='directiveName' but directive not in scope",
            "common_cases": [
                "ngForm: import FormsModule",
                "ngModel: import FormsModule",
                "matTooltip: import MatTooltipModule",
                "Custom directive: ensure imported in component/module"
            ],
            "solution": "Import the module that provides the directive"
        }
    },
    {
        "instruction": "Circular dependency warning",
        "error_type": "architecture",
        "response": {
            "status": "warning",
            "cause": "Module A imports Module B which imports Module A",
            "impact": "Can cause undefined errors, hard to maintain code",
            "solutions": [
                "Move shared code to separate module",
                "Use interfaces instead of concrete classes for typing",
                "Lazy load to break cycle",
                "Use forwardRef() if unavoidable",
                "Restructure to remove circular relationship"
            ],
            "prevention": "Plan module boundaries carefully, shared modules for common code"
        }
    },
    {
        "instruction": "ERROR in Maximum call stack size exceeded",
        "error_type": "infinite_loop",
        "response": {
            "status": "critical_error",
            "common_causes": [
                "Component rendering itself",
                "Infinite change detection cycle",
                "Recursive router navigation",
                "Circular service dependency causing infinite calls"
            ],
            "debugging": [
                "Check for component self-references in template",
                "Look for infinite subscriptions",
                "Check guards for redirect loops",
                "Use breakpoints to find recursive call"
            ]
        }
    },
    {
        "instruction": "NG0200: Circular dependency in DI detected",
        "error_type": "dependency_injection",
        "response": {
            "status": "error",
            "cause": "ServiceA depends on ServiceB which depends on ServiceA",
            "solutions": [
                "Use forwardRef(): inject(forwardRef(() => ServiceB))",
                "Restructure services to remove cycle",
                "Create intermediary service",
                "Use events/subjects instead of direct dependency"
            ],
            "best_practice": "Refactor to avoid circular dependencies"
        }
    },
    {
        "instruction": "Property 'X' does not exist on type 'Y'",
        "error_type": "typescript",
        "response": {
            "status": "type_error",
            "common_causes": [
                "Accessing property before async data loaded",
                "Wrong interface used",
                "Optional property accessed without check"
            ],
            "solutions": [
                "Use optional chaining: object?.property",
                "Add null check: if (object) { }",
                "Correct the interface definition",
                "Use non-null assertion if certain: object!.property"
            ]
        }
    },
    {
        "instruction": "ERROR in No provider for HttpClient",
        "error_type": "http_setup",
        "response": {
            "status": "missing_provider",
            "cause": "HttpClientModule not configured",
            "solutions": [
                "Standalone bootstrap: provideHttpClient() in app.config.ts",
                "NgModule: import HttpClientModule in AppModule",
                "For interceptors: withInterceptors() or withInterceptorsFromDi()"
            ],
            "code_example": "bootstrapApplication(AppComponent, { providers: [provideHttpClient()] })"
        }
    },
    {
        "instruction": "Router-outlet not rendering component",
        "error_type": "routing",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Verify <router-outlet> exists in template",
                "Check route path matches URL",
                "Ensure RouterModule is imported",
                "Check for typos in route paths",
                "Verify component is correctly specified in route"
            ],
            "debugging": [
                "Enable router tracing: enableTracing: true",
                "Log router events to see navigation",
                "Check browser console for errors"
            ]
        }
    },
    {
        "instruction": "Static injector error for token",
        "error_type": "dependency_injection",
        "response": {
            "status": "error",
            "cause": "Injecting service outside Angular context",
            "common_causes": [
                "Using inject() outside injection context",
                "Service used in function called outside Angular",
                "Factory provider without proper deps"
            ],
            "solutions": [
                "Pass injector to factory: Injector.create()",
                "Refactor to use service within injection context",
                "Use deps array in factory providers"
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

def format_code_response(language: str, code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": language,
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
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_command_response(task["command"], task["explanation"])
    } for task in ANGULAR_CLI_TASKS]

def generate_code_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": ex["instruction"],
        "response": format_code_response(ex["language"], ex["code"], ex["explanation"])
    } for ex in CODE_EXAMPLES]

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts]

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
    print("Generating Angular Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} CLI examples")
    
    code_examples = generate_code_examples()
    all_examples.extend(code_examples)
    print(f"Generated {len(code_examples)} code examples")
    
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
    
    output_file = output_dir / "angular.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
