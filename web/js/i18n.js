/**
 * PolyClash i18n – lightweight internationalization
 *
 * Usage:
 *   i18n.setLang('zh');
 *   i18n.t('view_0');  // => "琥珀洲"
 */

(function () {
    "use strict";

    var translations = {
        en: {
            // Game title
            game_title: "PolyClash",

            // View names (4 continents + 4 oceans)
            view_0: "Amberland",
            view_1: "Jadeland",
            view_2: "Goldenland",
            view_3: "Amethyst Land",
            view_4: "Coral Ocean",
            view_5: "Pearl Ocean",
            view_6: "Sapphire Ocean",
            view_7: "Obsidian Ocean",

            // UI
            score_black: "Black",
            score_white: "White",
            score_unclaimed: "Unclaimed",
            turn_black: "Black\u2019s turn",
            turn_white: "White\u2019s turn",
            move_label: "Move",
            status_welcome: "Welcome to PolyClash",
            status_start_game: "Start a game first.",
            status_illegal: "Illegal move.",
            status_not_turn: "Not your turn.",
            status_starting: "Starting game\u2026",
            status_local_started: "Local game started \u2013 you are Black.",
            status_you_black: "You are Black.",
            status_you_white: "You are White.",
            status_waiting: "Waiting for opponent\u2026",
            status_watching: "Watching the game.",
            status_invalid_key: "Invalid game key.",
            status_ai_passed: "AI passed.",
            status_ai_thinking: "AI is thinking\u2026",
            status_ai_mode: "AI mode",
            status_passed: "Player passed.",
            status_reset: "Game reset.",
            status_you_win: "You win!",
            status_you_lose: "You lose.",
            status_game_over: "Game over.",
            btn_local: "New Local Game",
            btn_pass: "Pass",
            btn_resign: "Resign",
            btn_reset: "Reset",
            btn_save: "Save Record",
            btn_network: "New Network Game",
            btn_join: "Join Game",
            label_server: "Server URL",
            prompt_token: "Enter server token:",
            prompt_role: "Enter role (black/white):",
        },

        "zh-Hans": {
            game_title: "\u661f\u9010",

            view_0: "\u7425\u73c0\u6d32",
            view_1: "\u7fe0\u7389\u6d32",
            view_2: "\u6d41\u91d1\u6d32",
            view_3: "\u7d2b\u6676\u6d32",
            view_4: "\u73ca\u745a\u6d0b",
            view_5: "\u73cd\u73e0\u6d0b",
            view_6: "\u84dd\u5b9d\u6d0b",
            view_7: "\u9ed1\u66dc\u6d0b",

            score_black: "\u9ed1\u65b9",
            score_white: "\u767d\u65b9",
            score_unclaimed: "\u672a\u5360",
            turn_black: "\u9ed1\u65b9\u843d\u5b50",
            turn_white: "\u767d\u65b9\u843d\u5b50",
            move_label: "\u624b\u6570",
            status_welcome: "\u6b22\u8fce\u6765\u5230\u661f\u9010",
            status_start_game: "\u8bf7\u5148\u5f00\u5c40\u3002",
            status_illegal: "\u975e\u6cd5\u843d\u5b50\u3002",
            status_not_turn: "\u8fd8\u6ca1\u8f6e\u5230\u672c\u65b9\u3002",
            status_starting: "\u6b63\u5728\u5f00\u5c40\u2026",
            status_local_started: "\u672c\u5730\u5bf9\u5c40\u5df2\u5f00\u59cb\uff0c\u672c\u65b9\u6267\u9ed1\u3002",
            status_you_black: "\u672c\u65b9\u6267\u9ed1\u3002",
            status_you_white: "\u672c\u65b9\u6267\u767d\u3002",
            status_waiting: "\u7b49\u5f85\u5bf9\u624b\u2026",
            status_watching: "\u89c2\u6218\u4e2d\u3002",
            status_invalid_key: "\u65e0\u6548\u7684\u6e38\u620f\u5bc6\u94a5\u3002",
            status_ai_passed: "AI \u5df2\u8df3\u8fc7\u3002",
            status_ai_thinking: "AI \u601d\u8003\u4e2d\u2026",
            status_ai_mode: "AI \u6258\u7ba1",
            status_passed: "\u73a9\u5bb6\u5df2\u8df3\u8fc7\u3002",
            status_reset: "\u5df2\u91cd\u7f6e\u3002",
            status_you_win: "\u672c\u65b9\u80dc\uff01",
            status_you_lose: "\u672c\u65b9\u8d1f\u3002",
            status_game_over: "\u5bf9\u5c40\u7ed3\u675f\u3002",
            btn_local: "\u672c\u5730\u5bf9\u5c40",
            btn_pass: "\u8df3\u8fc7",
            btn_resign: "\u8ba4\u8f93",
            btn_reset: "\u91cd\u7f6e",
            btn_save: "\u4fdd\u5b58\u68cb\u8c31",
            btn_network: "\u7f51\u7edc\u5bf9\u5c40",
            btn_join: "\u52a0\u5165",
            label_server: "\u670d\u52a1\u5668\u5730\u5740",
            prompt_token: "\u8bf7\u8f93\u5165\u670d\u52a1\u5668\u5bc6\u94a5\uff1a",
            prompt_role: "\u8bf7\u9009\u62e9\u89d2\u8272 (black/white)\uff1a",
        },

        "zh-Hant": {
            game_title: "\u661f\u9010",

            view_0: "\u7425\u73c0\u6d32",
            view_1: "\u7fe0\u7389\u6d32",
            view_2: "\u6d41\u91d1\u6d32",
            view_3: "\u7d2b\u6676\u6d32",
            view_4: "\u73ca\u745a\u6d0b",
            view_5: "\u73cd\u73e0\u6d0b",
            view_6: "\u85cd\u5bf6\u6d0b",
            view_7: "\u9ed1\u66dc\u6d0b",

            score_black: "\u9ed1\u65b9",
            score_white: "\u767d\u65b9",
            score_unclaimed: "\u672a\u4f54",
            turn_black: "\u9ed1\u65b9\u843d\u5b50",
            turn_white: "\u767d\u65b9\u843d\u5b50",
            move_label: "\u624b\u6578",
            status_welcome: "\u6b61\u8fce\u4f86\u5230\u661f\u9010",
            status_start_game: "\u8acb\u5148\u958b\u5c40\u3002",
            status_illegal: "\u975e\u6cd5\u843d\u5b50\u3002",
            status_not_turn: "\u9084\u6c92\u8f2a\u5230\u672c\u65b9\u3002",
            status_starting: "\u6b63\u5728\u958b\u5c40\u2026",
            status_local_started: "\u672c\u5730\u5c0d\u5c40\u5df2\u958b\u59cb\uff0c\u672c\u65b9\u57f7\u9ed1\u3002",
            status_you_black: "\u672c\u65b9\u57f7\u9ed1\u3002",
            status_you_white: "\u672c\u65b9\u57f7\u767d\u3002",
            status_waiting: "\u7b49\u5f85\u5c0d\u624b\u2026",
            status_watching: "\u89c0\u6230\u4e2d\u3002",
            status_invalid_key: "\u7121\u6548\u7684\u904a\u6232\u5bc6\u9470\u3002",
            status_ai_passed: "AI \u5df2\u8df3\u904e\u3002",
            status_ai_thinking: "AI \u601d\u8003\u4e2d\u2026",
            status_ai_mode: "AI \u8a17\u7ba1",
            status_passed: "\u73a9\u5bb6\u5df2\u8df3\u904e\u3002",
            status_reset: "\u5df2\u91cd\u7f6e\u3002",
            status_you_win: "\u672c\u65b9\u52dd\uff01",
            status_you_lose: "\u672c\u65b9\u8ca0\u3002",
            status_game_over: "\u5c0d\u5c40\u7d50\u675f\u3002",
            btn_local: "\u672c\u5730\u5c0d\u5c40",
            btn_pass: "\u8df3\u904e",
            btn_resign: "\u8a8d\u8f38",
            btn_reset: "\u91cd\u7f6e",
            btn_save: "\u5132\u5b58\u68cb\u8b5c",
            btn_network: "\u7db2\u8def\u5c0d\u5c40",
            btn_join: "\u52a0\u5165",
            label_server: "\u4f3a\u670d\u5668\u4f4d\u5740",
            prompt_token: "\u8acb\u8f38\u5165\u4f3a\u670d\u5668\u5bc6\u9470\uff1a",
            prompt_role: "\u8acb\u9078\u64c7\u89d2\u8272 (black/white)\uff1a",
        },

        ja: {
            game_title: "\u661f\u9010",

            view_0: "\u7425\u73c0\u5927\u9678",
            view_1: "\u7fe1\u7fe0\u5927\u9678",
            view_2: "\u9ec4\u91d1\u5927\u9678",
            view_3: "\u7d2b\u6c34\u6676\u5927\u9678",
            view_4: "\u73ca\u745a\u6d0b",
            view_5: "\u771f\u73e0\u6d0b",
            view_6: "\u30b5\u30d5\u30a1\u30a4\u30a2\u6d0b",
            view_7: "\u9ed2\u66dc\u77f3\u6d0b",

            score_black: "\u9ed2",
            score_white: "\u767d",
            score_unclaimed: "\u672a\u5360\u9818",
            turn_black: "\u9ed2\u306e\u756a",
            turn_white: "\u767d\u306e\u756a",
            move_label: "\u624b\u6570",
            status_welcome: "\u661f\u9010\u3078\u3088\u3046\u3053\u305d",
            status_you_black: "\u3042\u306a\u305f\u306f\u9ed2\u3002",
            status_you_white: "\u3042\u306a\u305f\u306f\u767d\u3002",
            status_waiting: "\u5bfe\u6226\u76f8\u624b\u3092\u5f85\u3063\u3066\u3044\u307e\u3059\u2026",
            status_watching: "\u89b3\u6226\u4e2d\u3002",
            status_invalid_key: "\u7121\u52b9\u306a\u30b2\u30fc\u30e0\u30ad\u30fc\u3002",
            status_ai_thinking: "AI \u601d\u8003\u4e2d\u2026",
            status_ai_mode: "AI \u30e2\u30fc\u30c9",
            status_you_win: "\u672c\u65b9\u306e\u52dd\u3061\uff01",
            status_you_lose: "\u672c\u65b9\u306e\u8ca0\u3051\u3002",
            status_game_over: "\u5bfe\u5c40\u7d42\u4e86\u3002",
            btn_local: "\u30ed\u30fc\u30ab\u30eb\u5bfe\u5c40",
            btn_pass: "\u30d1\u30b9",
            btn_resign: "\u6295\u4e86",
            btn_reset: "\u30ea\u30bb\u30c3\u30c8",
            btn_save: "\u68cb\u8b5c\u4fdd\u5b58",
        },

        ko: {
            game_title: "\u661f\u9010",

            view_0: "\ud638\ubc15 \ub300\ub959",
            view_1: "\ube44\ucde8 \ub300\ub959",
            view_2: "\ud669\uae08 \ub300\ub959",
            view_3: "\uc790\uc218\uc815 \ub300\ub959",
            view_4: "\uc0b0\ud638\uc591",
            view_5: "\uc9c4\uc8fc\uc591",
            view_6: "\uc0ac\ud30c\uc774\uc5b4\uc591",
            view_7: "\ud751\uc694\uc11d\uc591",

            score_black: "\ud751",
            score_white: "\ubc31",
            score_unclaimed: "\ubbf8\uc810\ub839",
            turn_black: "\ud751\uc758 \ucc28\ub840",
            turn_white: "\ubc31\uc758 \ucc28\ub840",
            move_label: "\uc218",
            status_welcome: "\u661f\u9010\uc5d0 \uc624\uc2e0 \uac83\uc744 \ud658\uc601\ud569\ub2c8\ub2e4",
            status_you_black: "\ub2f9\uc2e0\uc740 \ud751\uc785\ub2c8\ub2e4.",
            status_you_white: "\ub2f9\uc2e0\uc740 \ubc31\uc785\ub2c8\ub2e4.",
            status_waiting: "\uc0c1\ub300\ub97c \uae30\ub2e4\ub9ac\ub294 \uc911\u2026",
            status_watching: "\uad00\uc804 \uc911\u3002",
            status_invalid_key: "\uc798\ubabb\ub41c \uac8c\uc784 \ud0a4\u3002",
            status_ai_thinking: "AI \uc0ac\uace0 \uc911\u2026",
            status_ai_mode: "AI \ubaa8\ub4dc",
            status_you_win: "\uc2b9\ub9ac!",
            status_you_lose: "\ud328\ubc30.",
            status_game_over: "\uac8c\uc784 \uc885\ub8cc.",
            btn_local: "\ub85c\uceec \uac8c\uc784",
            btn_pass: "\ud328\uc2a4",
            btn_resign: "\uae30\uad8c",
            btn_reset: "\ub9ac\uc14b",
            btn_save: "\uae30\ubcf4 \uc800\uc7a5",
        },
    };

    var currentLang = "en";

    var i18n = {
        setLang: function (lang) {
            if (translations[lang]) {
                currentLang = lang;
            }
        },

        getLang: function () {
            return currentLang;
        },

        t: function (key) {
            var dict = translations[currentLang];
            if (dict && dict[key] !== undefined) {
                return dict[key];
            }
            // Fallback to English
            if (translations.en[key] !== undefined) {
                return translations.en[key];
            }
            return key;
        },

        availableLanguages: function () {
            return Object.keys(translations);
        },

        // Auto-detect language from browser
        detectLang: function () {
            var nav = (navigator.language || navigator.userLanguage || "en").toLowerCase();
            // Chinese: map region variants to script variants
            if (nav === "zh-tw" || nav === "zh-hk" || nav === "zh-hant") {
                currentLang = "zh-Hant";
            } else if (nav === "zh-cn" || nav === "zh-sg" || nav === "zh-hans" || nav.split("-")[0] === "zh") {
                currentLang = "zh-Hans";
            } else {
                var code = nav.split("-")[0];
                if (translations[code]) {
                    currentLang = code;
                }
            }
            return currentLang;
        },
    };

    window.i18n = i18n;
})();
