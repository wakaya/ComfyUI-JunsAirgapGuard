import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const I18N_TABLE = {
    en: {
        status_idle: "Idle",
        status_checking: "Checking...",
        status_reachable: "Reachable",
        status_unreachable: "Unreachable",
        status_invalid: "Invalid URL",

        mode_block_if_reachable: "Block if reachable",
        mode_block_if_unreachable: "Block if unreachable",
        mode_report_only: "Report only",
    },
    ja: {
        status_idle: "未確認",
        status_checking: "確認中...",
        status_reachable: "オンライン",
        status_unreachable: "オフライン",
        status_invalid: "URLが正しくない",

        mode_block_if_reachable: "オンラインなら停止",
        mode_block_if_unreachable: "オフラインなら停止",
        mode_report_only: "停止しない",
    },
};

const MODE_KEYS = [
    "block_if_reachable",
    "block_if_unreachable",
    "report_only",
];

function detectLanguage() {
    try {
        const comfyLocale =
            app.extensionManager?.setting?.get?.("Comfy.Locale") ??
            app.ui?.settings?.getSettingValue?.("Comfy.Locale");

        if (comfyLocale && comfyLocale !== "auto") {
            const lower = String(comfyLocale).toLowerCase();
            if (lower.startsWith("ja")) {
                return "ja";
            }
            return "en";
        }
    } catch (error) {
        // fallback to browser language below
    }

    const langs = [
        ...(navigator.languages || []),
        navigator.language || "en",
    ].filter(Boolean);

    for (const lang of langs) {
        const lower = String(lang).toLowerCase();
        if (lower.startsWith("ja")) {
            return "ja";
        }
    }

    return "en";
}

function getI18n() {
    const lang = detectLanguage();
    return I18N_TABLE[lang] || I18N_TABLE.en;
}

function getModeLabel(modeKey, lang = detectLanguage()) {
    const table = I18N_TABLE[lang] || I18N_TABLE.en;
    switch (modeKey) {
        case "block_if_reachable":
            return table.mode_block_if_reachable;
        case "block_if_unreachable":
            return table.mode_block_if_unreachable;
        case "report_only":
            return table.mode_report_only;
        default:
            return modeKey;
    }
}

function normalizeModeValue(value) {
    if (value == null) {
        return "block_if_reachable";
    }

    const str = String(value).trim();

    if (MODE_KEYS.includes(str)) {
        return str;
    }

    const aliases = {
        "オンラインなら停止": "block_if_reachable",
        "オフラインなら停止": "block_if_unreachable",
        "停止しない": "report_only",

        "Block if reachable": "block_if_reachable",
        "Block if unreachable": "block_if_unreachable",
        "Report only": "report_only",
    };

    return aliases[str] || "block_if_reachable";
}

function getLocalizedModeValues(lang = detectLanguage()) {
    return MODE_KEYS.map((key) => getModeLabel(key, lang));
}

function findWidgetByName(node, name) {
    return node?.widgets?.find((w) => w.name === name);
}

function localizeModeWidget(node) {
    const widget = findWidgetByName(node, "mode");
    if (!widget) {
        return;
    }

    if (!widget.__junsAirgapGuardPatched) {
        widget.__junsAirgapGuardPatched = true;

        const originalCallback = widget.callback;
        const originalSerializeValue = widget.serializeValue;

        widget.callback = function (...args) {
            const selected = args[0];
            const canonical = normalizeModeValue(selected);
            const lang = detectLanguage();

            this.value = getModeLabel(canonical, lang);

            if (typeof originalCallback === "function") {
                return originalCallback.call(this, canonical, ...args.slice(1));
            }
        };

        widget.serializeValue = function (...args) {
            const canonical = normalizeModeValue(this.value);

            if (typeof originalSerializeValue === "function") {
                const result = originalSerializeValue.apply(this, args);
                if (result != null && result !== this.value) {
                    return normalizeModeValue(result);
                }
            }

            return canonical;
        };
    }

    const lang = detectLanguage();
    const canonical = normalizeModeValue(widget.value);

    if (!widget.options) {
        widget.options = {};
    }

    widget.options.values = getLocalizedModeValues(lang);
    widget.value = getModeLabel(canonical, lang);
}

function getStatusView(status) {
    const I18N = getI18n();

    if (!status || !status.state || status.state === "idle") {
        return { text: I18N.status_idle, bg: "#666666" };
    }

    switch (status.state) {
        case "checking":
            return { text: I18N.status_checking, bg: "#a67c00" };
        case "reachable":
            return { text: I18N.status_reachable, bg: "#2e8b57" };
        case "unreachable":
            return { text: I18N.status_unreachable, bg: "#b22222" };
        case "invalid":
            return { text: I18N.status_invalid, bg: "#8b008b" };
        default:
            return { text: I18N.status_idle, bg: "#666666" };
    }
}

app.registerExtension({
    name: "juns.airgap_guard.status_and_i18n",

    setup() {
        api.addEventListener("juns_airgap_guard_status", (event) => {
            const detail = event.detail;
            const node = app.graph?.getNodeById?.(Number(detail.node_id));
            if (!node) {
                return;
            }

            node.__junsAirgapGuardStatus = detail;

            if (typeof node.setDirtyCanvas === "function") {
                node.setDirtyCanvas(true, true);
            }

            app.graph?.setDirtyCanvas?.(true, true);
        });
    },

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "JunsAirgapGuard") {
            return;
        }

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated
                ? originalOnNodeCreated.apply(this, arguments)
                : undefined;

            localizeModeWidget(this);
            return result;
        };

        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalOnConfigure
                ? originalOnConfigure.apply(this, arguments)
                : undefined;

            localizeModeWidget(this);
            return result;
        };

        const originalOnDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            localizeModeWidget(this);

            if (originalOnDrawForeground) {
                originalOnDrawForeground.apply(this, arguments);
            }

            const status = this.__junsAirgapGuardStatus || { state: "idle" };
            const view = getStatusView(status);

            const x = 10;
            const y = this.size[1] - 30;
            const h = 20;
            const paddingX = 8;

            ctx.save();
            ctx.font = "12px sans-serif";
            ctx.textBaseline = "middle";

            const textWidth = Math.ceil(ctx.measureText(view.text).width);
            const w = textWidth + paddingX * 2;

            ctx.fillStyle = view.bg;
            ctx.fillRect(x, y, w, h);

            ctx.strokeStyle = "rgba(0,0,0,0.35)";
            ctx.strokeRect(x, y, w, h);

            ctx.fillStyle = "#ffffff";
            ctx.fillText(view.text, x + paddingX, y + h / 2);

            ctx.restore();
        };
    },
});
