export const translations = {
    en: {
        common: {
            appName: "BOOTH-Lens",
            pricing: "Pricing",
            optOut: "Opt-out",
            backToHome: "Back to Home",
            loading: "Loading...",
            submit: "Submit",
            submitting: "Submitting...",
            submitted: "Submitted",
            error: "Error",
            cancel: "Cancel",
            search: "Search",
            support: "Support",
        },
        home: {
            titlePrimary: "Find",
            titleAccent: "Perfect",
            titleSecondary: "BOOTH Items.",
            subtitle: "Upload an image to find the exact BOOTH items used.",
            uploadPlaceholder: "Click or drag image here",
            uploadSupport: "Supports JPG, PNG, WEBP",
            searchPlaceholder: "Describe what you are looking for...",
            analyzing: "Analyzing image...",
            failedSearch: "Failed to search. Please try again.",
            noResults: "Simple. Fast. Accurate.",
            match: "Match",
            viewOnBooth: "View on BOOTH",
            searchResults: "Search Results",
            matches: "Matches",
            features: {
                analysis: {
                    title: "Instant Analysis",
                    desc: "Our advanced CLIP-based AI analyzes your images in milliseconds to find the perfect match."
                },
                search: {
                    title: "Cross-Shop Search",
                    desc: "Search across all authorized BOOTH shops simultaneously for VRChat assets and textures."
                },
                secure: {
                    title: "Secure & Safe",
                    desc: "Transparency and privacy are our top priorities. Authorized items only, with robust opt-out features."
                }
            },
            footer: {
                rights: "All rights reserved.",
                privacy: "Privacy Policy",
                terms: "Terms of Service"
            }
        },
        pricing: {
            title: "Simple Pricing",
            subtitle: "Choose the plan that fits your needs.",
            free: "Free",
            freePrice: "¥0",
            premium: "Premium",
            premiumPrice: "¥980",
            perMonth: "/month",
            popular: "POPULAR",
            currentPlan: "Current Plan",
            upgradeNow: "Upgrade Now",
            processing: "Processing...",
            features: {
                free: {
                    searchLimit: "3 Searches per month",
                    basicResults: "Basic search results",
                    deepLogic: "Deep search logic",
                },
                premium: {
                    unlimited: "Unlimited Searches",
                    fullResults: "Full search results",
                    advancedFilters: "Advanced filters (Clothes only)",
                    directLinks: "Direct shop links",
                },
            },
        },
        optOut: {
            title: "Opt-out Request",
            description: "If you are a shop owner and wish to remove your items from BOOTH-Lens search results, please enter your shop URL below. Processing takes up to 48 hours.",
            label: "BOOTH Shop URL",
            placeholder: "https://your-shop.booth.pm",
            success: "Request submitted successfully. We will process it shortly.",
            failed: "Failed to submit request. Please try again.",
        },
        terms: {
            title: "Terms of Service",
            updated: "Last Updated: February 18, 2026",
            introduction: "These Terms of Service (hereinafter referred to as the 'Terms') set forth the conditions for using 'BOOTH-Lens' (this Service) provided by 'Mamemame-an' (hereinafter referred to as the 'Shop'). By using this Service, users are deemed to have agreed to these Terms.",
            sections: [
                {
                    title: "1. Service Description",
                    content: "BOOTH-Lens is an AI-powered visual search engine that allows users to find products on the BOOTH marketplace using images. We provide search and discovery functionality for VRChat assets and creative works. The Shop does not sell items directly through this search interface."
                },
                {
                    title: "2. Compliance with BOOTH Guidelines",
                    content: "This Service operates in accordance with the 'BOOTH Guidelines' (https://booth.pm/guidelines) set by pixiv Inc. The Shop respects the community standards and intellectual property rights established by the BOOTH platform."
                },
                {
                    title: "3. Data Collection and Legality",
                    content: "In compliance with Article 30-4 of the Japanese Copyright Act, this Service collects publicly available product data from BOOTH for the purpose of 'Information Analysis.' This is done to improve search convenience and contribute to the healthy development of creative activities, as permitted under BOOTH's scraping policy. The Shop uses low-resolution thumbnail images only for search identification purposes."
                },
                {
                    title: "4. AI Usage and Accuracy",
                    content: "This Service utilizes AI models (CLIP and YOLO) to analyze visual features. While the Shop strives for high accuracy, search results are generated algorithmically. We do not guarantee that results will always be 100% accurate."
                },
                {
                    title: "5. Shop Owner Rights & Opt-out",
                    content: "The Shop provides an 'Opt-out' mechanism for shop owners who do not wish to have their products indexed. Upon verification of a request, the Shop will remove the specified shop's data from our index within 48 hours."
                },
                {
                    title: "6. Prohibited Actions",
                    content: "Users are prohibited from:\n\n• Reverse engineering or analyzing the AI models.\n• Placing excessive load on servers through automated searches.\n• Using the Service for illegal activities or in any way that violates Pixiv/BOOTH's terms."
                }
            ]
        },
        privacy: {
            title: "Privacy Policy",
            introduction: "BOOTH-Lens (hereinafter referred to as 'this Service'), operated by 'Mamemame-an' (the Shop), establishes this Privacy Policy to ensure the safe and proper handling of user data. We are committed to protecting your privacy and being transparent about how we use your information.",
            sections: [
                {
                    title: "1. Information We Collect",
                    content: "To provide the best searching experience, the Shop collects the following types of information:\n\n• Images uploaded for search: Used temporarily for analysis and deleted shortly after processing.\n• Email and Payment Data: Collected via Stripe for Premium subscribers. The Shop never stores credit card details directly on our servers.\n• Usage Logs: Anonymous data such as search timestamps and browser types to improve our AI performance."
                },
                {
                    title: "2. Purpose of Information Use",
                    content: "The collected information is used strictly for the following purposes:\n\n• Executing image-based product searches.\n• Managing subscriptions and processing payments via Stripe.\n• Preventing unauthorized use and maintaining server security.\n• Analyzing anonymous data to refine our search algorithms."
                },
                {
                    title: "3. Third-Party Data Sharing",
                    content: "The Shop does not sell your personal information. Data is shared with third parties only when necessary:\n\n• Stripe: For secure payment processing (handled under Stripe's privacy policy).\n• Cloudflare: For secure image data transmission and hosting (handled under Cloudflare's privacy policy)."
                },
                {
                    title: "4. Cookies and Session Data",
                    content: "This Service uses cookies to remember your language preferences and maintain search sessions. You can disable cookies in your browser settings, though some features may not function correctly."
                }
            ]
        }
    },
    ja: {
        common: {
            appName: "BOOTH-Lens",
            pricing: "料金プラン",
            optOut: "オプトアウト",
            backToHome: "ホームに戻る",
            loading: "読み込み中...",
            submit: "送信",
            submitting: "送信中...",
            submitted: "送信済み",
            error: "エラー",
            cancel: "キャンセル",
            search: "検索",
            support: "支援する",
        },
        home: {
            titlePrimary: "理想の",
            titleAccent: "BOOTHアイテム",
            titleSecondary: "を、一瞬で見つける。",
            subtitle: "画像をアップロードして、使用されているBOOTHアイテムを特定します。",
            uploadPlaceholder: "ここをクリックまたは画像をドラッグ",
            uploadSupport: "JPG, PNG, WEBP 対応",
            searchPlaceholder: "何をお探しですか？",
            analyzing: "画像を解析中...",
            failedSearch: "検索に失敗しました。もう一度お試しください。",
            noResults: "シンプル。高速。高精度。",
            match: "一致率",
            viewOnBooth: "BOOTHで見る",
            searchResults: "検索結果",
            matches: "件の一致",
            features: {
                analysis: {
                    title: "瞬時な解析",
                    desc: "高度なCLIPベースのAIが、ミリ秒単位で画像を解析し、最適なマッチングを見つけ出します。"
                },
                search: {
                    title: "広範なインデックス検索",
                    desc: "BOOTH上の膨大な公開商品データを横断的に検索し、VRChatアセットやテクスチャを特定します。"
                },
                secure: {
                    title: "安全・安心",
                    desc: "透明性と法遵守を最優先。クリエイターの権利を尊重し、オプトアウト機能も完備しています。"
                }
            },
            footer: {
                rights: "All rights reserved.",
                privacy: "プライバシーポリシー",
                terms: "利用規約"
            }
        },
        pricing: {
            title: "シンプルな料金プラン",
            subtitle: "あなたに合ったプランを選んでください。",
            free: "フリー",
            freePrice: "¥0",
            premium: "プレミアム",
            premiumPrice: "¥980",
            perMonth: "/月",
            popular: "人気",
            currentPlan: "現在のプラン",
            upgradeNow: "アップグレード",
            processing: "処理中...",
            features: {
                free: {
                    searchLimit: "月3回まで検索可能",
                    basicResults: "基本的な検索結果",
                    deepLogic: "高度な検索ロジック",
                },
                premium: {
                    unlimited: "無制限の検索",
                    fullResults: "すべての検索結果を表示",
                    advancedFilters: "高度なフィルター（衣装のみ等）",
                    directLinks: "ショップへの直接リンク",
                },
            },
        },
        optOut: {
            title: "オプトアウト申請",
            description: "ショップオーナー様で、BOOTH-Lens検索結果からの除外をご希望の場合は、以下のフォームにショップURLを入力してください。対応には最大48時間かかります。",
            label: "BOOTH ショップURL",
            placeholder: "https://your-shop.booth.pm",
            success: "申請を受け付けました。順次対応いたします。",
            failed: "申請の送信に失敗しました。もう一度お試しください。",
        },
        terms: {
            title: "利用規約",
            updated: "最終更新日: 2026年2月18日",
            introduction: "本利用規約（以下「本規約」）は、「豆々庵」（以下「当ショップ」）が提供する「BOOTH-Lens」（以下「本サービス」）の利用条件を定めるものです。本サービスを利用することにより、ユーザーは本規約に同意したものとみなされます。",
            sections: [
                {
                    title: "1. サービスの内容",
                    content: "BOOTH-Lensは、AI技術を用いてBOOTH上の商品を画像から検索できるビジュアル検索エンジンです。VRChat向けアセット等の創作物の発見をサポートすることを目的としており、商品の直接的な販売は行いません。"
                },
                {
                    title: "2. BOOTHガイドラインの遵守",
                    content: "本サービスは、ピクシブ株式会社が定める「BOOTHガイドライン」（https://booth.pm/guidelines）を遵守して運営されています。当ショップは、プラットフォームが定めるコミュニティ基準および知的財産権の保護方針を尊重します。"
                },
                {
                    title: "3. データ収集の正当性",
                    content: "本サービスは、日本の著作権法第30条の4（情報解析のための複製等）に基づき、情報解析を目的としてBOOTH上の公開情報を収集しています。これは、BOOTHのスクレイピング方針における「ユーザーの利便性向上や創作活動の健全な発展に資することを目的とした情報解析」に該当します。また、当ショップが検索補助のために使用する低解像度サムネイルは、検索エンジンの適正な利用範囲内として扱われます。"
                },
                {
                    title: "4. AIによる解析の特性と免責",
                    content: "本サービスはAIモデル（CLIPおよびYOLO）を用いて解析を行います。精度の向上に努めておりますが、結果はアルゴリズムにより自動生成されるため、常に100%の正確性やユーザーの期待との一致を当ショップが保証するものではありません。"
                },
                {
                    title: "5. ショップオーナーの権利とオプトアウト",
                    content: "当ショップは、権利者様の意向を尊重し、検索インデックスへの登録を希望されないショップオーナー様向けに「オプトアウト申請」を設けています。申請をいただいた場合、速やかに（通常48時間以内）該当ショップのデータを削除します。"
                },
                {
                    title: "6. 禁止行為",
                    content: "利用者は以下の行為を行ってはなりません：\n\n• AIモデルの逆解析やリバースエンジニアリング\n• 自動検索等によるサーバーへの過度な負荷\n• その他、BOOTHやpixivの規約に抵触する不正な利用"
                }
            ]
        },
        privacy: {
            title: "プライバシーポリシー",
            introduction: "「豆々庵」（以下「当ショップ」）が運営するBOOTH-Lens（以下「本サービス」）は、ユーザーの皆様の情報を安全かつ適切に取り扱うため、以下のプライバシーポリシーを定めます。当ショップはプライバシー保護に真摯に取り組み、情報の透明性を確保します。",
            sections: [
                {
                    title: "1. 取得する情報",
                    content: "当ショップでは、以下の情報を取得・利用します：\n\n・検索のためにアップロードされた画像：解析のために一時的に使用され、処理完了後速やかに破棄されます。\n・メールアドレスおよび決済情報：有料プランご契約時にStripeを通じて取得します。クレジットカード情報は当ショップのサーバーには保存されません。\n・利用ログ：AIの精度向上およびセキュリティ維持のため、匿名化された検索日時やブラウザ情報を記録します。"
                },
                {
                    title: "2. 利用目的",
                    content: "取得した情報は、以下の目的のみに使用します：\n\n・画像を用いた商品検索機能の提供。\n・有料プランの購読管理およびStripeを通じた決済処理。\n・不正アクセスの防止およびサーバーの安定稼働。\n・統計データの分析による、検索アルゴリズムの改善。"
                },
                {
                    title: "3. 第三者への情報提供",
                    content: "当ショップはユーザーの個人情報を販売しません。以下の場合を除き、本人の同意なく第三者に提供することはありません：\n\n・Stripe：安全な決済処理を委託するため（Stripeのプライバシーポリシーに従い運営されます）。\n・Cloudflare：画像の安全な転送およびホスティングのため（Cloudflareのプライバシーポリシーに従い運営されます）。"
                },
                {
                    title: "4. クッキー（Cookie）とセッションデータ",
                    content: "本サービスでは、言語設定の保存やセッション維持のためにクッキーを利用します。ブラウザの設定でクッキーを無効にすることも可能ですが、一部の機能が制限される場合があります。"
                }
            ]
        }
    }
};

export type Language = "en" | "ja";
export type Translation = typeof translations.en;
