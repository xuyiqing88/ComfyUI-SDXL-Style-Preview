import { app } from "../../../scripts/app.js";
app.registerExtension({
	name: "preview.ContextMenuHook",
	init() {
		const getOrSet = (target, name, create) => {
			if (name in target) return target[name];
			return (target[name] = create());
		};
		const symbol = getOrSet(window, "__preview__", () => Symbol("__preview__"));
		const store = getOrSet(window, symbol, () => ({}));
		const contextMenuHook = getOrSet(store, "contextMenuHook", () => ({}));
		for (const e of ["ctor", "preAddItem", "addItem"]) {
			if (!contextMenuHook[e]) {
				contextMenuHook[e] = [];
			}
		}

		// Big ol' hack to get allow customizing the context menu
		// Replace the addItem function with our own that wraps the context of "this" with a proxy
		// That proxy then replaces the constructor with another proxy
		// That proxy then calls the custom ContextMenu that supports filters
		const ctorProxy = new Proxy(LiteGraph.ContextMenu, {
			construct(target, args) {
				return new LiteGraph.ContextMenu(...args);
			},
		});

		function triggerCallbacks(name, getArgs, handler) {
			const callbacks = contextMenuHook[name];
			if (callbacks && callbacks instanceof Array) {
				const args = getArgs.call(this); // 修改这一点以确保 getArgs 能接收正确的 this 上下文
				for (const cb of callbacks) {
					const r = cb.apply(this, args); // 使用 apply 来传递正确的 this 上下文
					handler?.call(this, r); // 同上
				}
			} else {
				console.warn("[pysssss 🐍]", `invalid ${name} callbacks`, callbacks, name in contextMenuHook);
			}
		}
		

		const originalAddItem = LiteGraph.ContextMenu.prototype.addItem;
LiteGraph.ContextMenu.prototype.addItem = function () {
    const proxy = new Proxy(this, {
        get(target, prop) {
            if (prop === "constructor") {
                return ctorProxy;
            }
            return target[prop];
        },
    });
    proxy.__target__ = this;

    let el;
    let args = arguments;
    triggerCallbacks(
        "preAddItem",
        () => [el, this, args],
        (r) => {
            if (r !== undefined) el = r;
        }
    );

    // 确保调用原始的 addItem 方法，避免递归
    if (el === undefined) {
        el = originalAddItem.apply(this, arguments);
    }

    triggerCallbacks(
        "addItem",
        () => [el, this, args],
        (r) => {
            if (r !== undefined && r instanceof HTMLElement) {
                el = r;
            }
        }
    );

    return el;
};

		// We also need to patch the ContextMenu constructor to unwrap the parent else it fails a LiteGraph type check
		const originalContextMenuCtor = LiteGraph.ContextMenu;
		LiteGraph.ContextMenu = function (values, options) {
			// 确保 options 是一个对象，并且 parentMenu 是 ContextMenu 的实例
			if (options && options.parentMenu && !(options.parentMenu instanceof LiteGraph.ContextMenu)) {
				console.warn("parentMenu is not an instance of ContextMenu, ignoring it.");
				options.parentMenu = null;
			}
		
			// 直接使用原始构造函数创建 ContextMenu 实例
			const contextMenuInstance = new originalContextMenuCtor(values, options);
		
			// 触发构造函数钩子，确保使用正确的 this 上下文
			triggerCallbacks.call(contextMenuInstance, "ctor", () => [values, options]);
		
			return contextMenuInstance;
		};
		
		// 确保新的 ContextMenu 原型链指向原始的 ContextMenu 原型
		LiteGraph.ContextMenu.prototype = originalContextMenuCtor.prototype;
	},
});