# REROUTES

再生可能エネルギー情報提供システム【REPOS（リーポス）】（http://www.renewable-energy-potential.env.go.jp/RenewableEnergy/ ）からデータをダウンロードし、高空間解像度の再生可能エネルギーポテンシャルマップを作成するためのコードです。

（注）2021/07/25現在、データをダウンロードするコードのみ公開中です。2分の1標準メッシュに按分・集計するコードは後日公開いたします。

# 利用上の注意
再生可能エネルギー情報提供システム【REPOS（リーポス）】（http://www.renewable-energy-potential.env.go.jp/RenewableEnergy/ ）（以下、REPOS）、国土数値情報ダウンロードサイト（https://nlftp.mlit.go.jp/ksj/index.html ）、および政府統計の総合窓口(e-Stat)（https://www.e-stat.go.jp/ ）提供のデータを利用します。本レポジトリのコードを利用する際は、各データの規約をご確認の上ご利用ください。

# 利用方法
- scriptディレクトリ以下のコードをダウンロードしてご利用ください。詳細は [Wiki](https://github.com/Green-Engineers-Lab/REROUTES/wiki) をご参照ください。
- コードの実行には、ArcPyを利用可能なPython v3.Xの実行環境が必要です (2021/07/25現在)。
- 大量のデータをダウンロードするため、1. サーバーに負荷のかからない夜間にダウンロードしていただくとともに、2. time.sleep()の待ち時間を短縮しないようご注意ください。
- 本コードでの処理は、2021/07/25現在の元データのデータフォーマットに依存しています。データの仕様変更などを発見されましたら、[issues](https://github.com/Green-Engineers-Lab/REROUTES/issues) からお知らせいただけると幸いです。

# 出典
- 環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書: http://www.renewable-energy-potential.env.go.jp/RenewableEnergy/report/r01.html (アクセス日2021.05.18)
- 環境省，再生可能エネルギー情報提供システム[REPOS(リーポス)] : http://www.renewable-energy-potential.env.go.jp/RenewableEnergy/index.html (アクセス日2021.05.31)
- 国土交通省，国土数値情報ダウンロード: https://nlftp.mlit.go.jp/ksj/index.html (アクセス日2021.04.28)
<!-- - 総務省，公共施設状況調経年比較表2017: https://www.soumu.go.jp/iken/shisetsu/index.html (アクセス日2021.05.19)
- 文部科学省，文部科学統計要覧 (平成23年版): https://warp.ndl.go.jp/info:ndljp/pid/11293659/www.mext.go.jp/b_menu/toukei/002/002b/1305705.htm (アクセス日2021.05.19)
- 環境省，第5回基礎調査河川調査報告書: http://www.biodic.go.jp/reports2/5th/kasen/5_kasen.pdf (アクセス日2021.05.26) -->
- K. Hori, T. Matsui, T. Hasuike, K. Fukui, T. Machimura: Development and Application of the Renewable Energy Regional Optimization Utility Tool for Environmental Sustainability: REROUTES, Renewable Energy, 93,(2016), pp548-561,
- 堀啓子，松井孝典，小野智司，福井健一，蓮池隆，町村尚：地域別再生可能エネルギーミックスの多目的最適化ツールの開発と応用，人工知能学会論文集，33-3(2018), p. F-SGAI01_1-11
- K Hori, J Kim, R Kawase, M Kimura, T Matsui, and T Machimura，Local Energy System Design Support using a Renewable Energy Mix Multi-objective Optimization Model and a Co-Creative Optimization Process, Renewable Energy, 156 (2020), pp1278-1291

