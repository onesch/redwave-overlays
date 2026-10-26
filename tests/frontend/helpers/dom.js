// Minimal DOM doubles for renderer and settings-page tests: `new FakeDocument({ id: 'class' })`
// builds the markup under test, then `element.click()` / `setValue()` drive it like the real DOM.

class FakeClassList {
  constructor(names = '') {
    this.names = new Set(names.split(/\s+/).filter(Boolean));
  }

  add(...names) { names.forEach((name) => this.names.add(name)); }
  remove(...names) { names.forEach((name) => this.names.delete(name)); }
  contains(name) { return this.names.has(name); }

  // Used by the settings page widgets: `toggle(name, force)`.
  toggle(name, force) {
    const active = force ?? !this.names.has(name);
    if (active) this.names.add(name);
    else this.names.delete(name);
    return active;
  }
}

const CANVAS_METHODS = [
  'clearRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fill', 'fillRect',
  'setTransform', 'save', 'restore', 'closePath', 'arc',
];

function createContext2D() {
  const context = {};
  CANVAS_METHODS.forEach((name) => { context[name] = () => {}; });
  return context;
}

class FakeElement {
  constructor({ id = '', className = '', tag = 'div', document = null } = {}) {
    this.document = document;
    this.tagName = tag.toUpperCase();
    this.id = id;
    this.style = { setProperty: (name, value) => { this.style[name] = value; } };
    this.dataset = {};
    this.children = [];
    this.listeners = new Map();
    this.rect = { width: 300, height: 100, left: 0, top: 0 };
    this.textContent = '';
    this.innerText = '';
    this.innerHTML = '';
    this.value = '';
    this.src = '';
    this.removed = false;
    this.className = className;
  }

  set className(value) {
    this._className = value;
    this.classList = new FakeClassList(value);
  }

  get className() { return this._className; }

  // Form controls stringify their value, like the DOM does.
  set value(value) { this._value = String(value); }
  get value() { return this._value; }

  // Elements created by a renderer are usually appended to another element,
  // and the document then resolves them by id, as in the real DOM.
  get parentElement() {
    return this._parentElement ?? this.document?.body ?? null;
  }

  set parentElement(element) { this._parentElement = element; }

  appendChild(child) {
    this.children.push(child);
    child.parentElement = this;
    if (child.id) this.document?.elements.set(child.id, child);
    return child;
  }

  remove() {
    this.removed = true;
    if (this.id && this.document?.elements.get(this.id) === this) {
      this.document.elements.delete(this.id);
    }
  }

  // Child queries (e.g. `row.querySelector('.pos')`) are not modelled; tests
  // register the selectors they need on the document instead.
  querySelector() { return null; }
  querySelectorAll() { return []; }
  getBoundingClientRect() { return { ...this.rect }; }
  getContext() { return this.context ??= createContext2D(); }

  // `addEventListener` + `emit` replace event dispatch for tests.
  addEventListener(type, handler) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), handler]);
  }

  emit(type, payload = {}) {
    (this.listeners.get(type) ?? []).forEach((handler) => handler(payload));
  }

  click() { this.emit('click'); }

  // Set the control value and fire the event the widgets listen to.
  setValue(value, type = 'input') {
    this.value = value;
    this.emit(type);
  }
}

class FakeDocument {
  // `elements` maps ids to class names, mirroring the markup under test.
  // `document.body` doubles as the `.overlay-body` element.
  constructor(elements = {}) {
    this.elements = new Map();
    this.selectors = new Map();
    this.body = this.add(new FakeElement({ id: 'overlay-body', tag: 'body', document: this }));
    this.documentElement = new FakeElement({ tag: 'html', document: this });

    Object.entries(elements).forEach(([id, className]) => {
      this.add(new FakeElement({ id, className, document: this }));
    });

    this.registerSelector('.overlay-body', this.body);
  }

  add(element) {
    this.elements.set(element.id, element);
    return element;
  }

  createElement(tag = 'div') {
    return new FakeElement({ tag, document: this });
  }

  getElementById(id) { return this.elements.get(id) ?? null; }
  querySelector(selector) { return this.selectors.get(selector) ?? null; }
  querySelectorAll() { return []; }

  // Map a CSS selector (e.g. `.radar-container`) onto one of the elements.
  registerSelector(selector, elementOrId) {
    this.selectors.set(
      selector,
      typeof elementOrId === 'string' ? this.getElementById(elementOrId) : elementOrId,
    );
    return this;
  }
}

class FakeWindow {
  constructor({ devicePixelRatio = 1 } = {}) {
    this.devicePixelRatio = devicePixelRatio;
    this.listeners = new Map();
  }

  getComputedStyle() {
    return { getPropertyValue: () => '#fff' };
  }

  addEventListener(type, handler) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), handler]);
  }

  emit(type) {
    (this.listeners.get(type) ?? []).forEach((handler) => handler());
  }
}

module.exports = { FakeDocument, FakeWindow };
