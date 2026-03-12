import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const FALLBACK_STRINGS = {
    status_idle: "Idle",
    status_checking: "Checking...",
    status_reachable: "Reachable",
    status_unreachable: "Unreachable",
    status_invalid: "Invalid URL",
};

let I18N = { ...FALLBACK_STRINGS };

function detectLanguage() {
    const langs = [
        ...(navigator.languages || []),
        navigator.language || "en",
    ].filter(Boolean);

    for (const lang of langs) {
        const lower = String(lang).toLowerCase();
        if (lower.startsWith("ja")) return "ja";
    }
    return "en";
}

async function loadI18n() {
    const lang = detectLanguage();
    const candidates = [lang, "en"];

    for (const candidate of candidates) {
        try {
            const url = new URL(`../../locales/${candidate}/main.json`, import.meta.url);
            const res = await fetch(url);
            if (!res.ok) continue;
            const data = await res.json();
            I18N = { ...FALLBACK_STRINGS, ...data };
            return;
        } catch {
            // ignore and try fallback
        }
    }
}

function getStatusView(status) {
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
    name: "juns.airgap_guard.status",

    async setup() {
        await loadI18n();

        api.addEventListener("juns_airgap_guard_status", (event) => {
            const detail = event.detail;
            const node = app.graph?.getNodeById?.(Number(detail.node_id));
            if (!node) return;

            node.__junsAirgapGuardStatus = detail;

            if (typeof node.setDirtyCanvas === "function") {
                node.setDirtyCanvas(true, true);
            }
            app.graph?.setDirtyCanvas?.(true, true);
        });
    },

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "JunsAirgapGuard") return;

        const onDrawForeground = nodeType.prototype.onDrawForeground;

        nodeType.prototype.onDrawForeground = function (ctx) {
            if (onDrawForeground) {
                onDrawForeground.apply(this, arguments);
            }

            const status = this.__junsAirgapGuardStatus || { state: "idle" };
            const view = getStatusView(status);

            const x = 10;
            const y = this.size[1] - 30;
            const h = 20;
            const px = 8;

            ctx.save();
            ctx.font = "12px sans-serif";
            ctx.textBaseline = "middle";

            const textWidth = Math.ceil(ctx.measureText(view.text).width);
            const w = textWidth + px * 2;

            ctx.fillStyle = view.bg;
            ctx.fillRect(x, y, w, h);

            ctx.strokeStyle = "rgba(0,0,0,0.35)";
            ctx.strokeRect(x, y, w, h);

            ctx.fillStyle = "#ffffff";
            ctx.fillText(view.text, x + px, y + h / 2);

            ctx.restore();
        };
    },
});
