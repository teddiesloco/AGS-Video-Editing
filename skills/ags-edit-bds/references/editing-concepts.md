# ags-edit-bds — 5 concept dựng (chọn một, nói rõ cho người dùng)

Dùng khi người dùng chưa nói rõ phong cách, hoặc nói "đẹp hơn / chuyên nghiệp hơn / như editor YouTube". Đây là **hướng dẫn
quyết định cho agent**, không phải luật và không phải tính năng mới của engine. Engine chỉ làm được những gì `SKILL.md` ghi
(`render`, `--zoom`, `--grade`, `--transition`, `--seconds`/`--beat-step`, `ags_editorial_sub.py`, `ags_sfx.py`); mọi con số dưới
đây là **heuristic để thử rồi soát bằng mắt**, không phải chuẩn đã đo và không bảo đảm hiệu quả/viral.

## 0. Nguyên tắc chung (đọc trước khi chọn concept)
- **Cảm xúc đích trước, kỹ thuật sau.** Viết một câu: "người xem xong video này cảm thấy / làm gì". Mọi lựa chọn bên dưới phải
  phục vụ câu đó; không hợp thì bỏ.
- **Cùng một grade ≠ khớp màu.** `--grade natural|warm` chỉ áp một công thức giống nhau cho mọi clip để bớt lệch rõ; nó **không**
  cân bằng trắng, không khớp độ sáng/da giữa clip quay khác máy, khác giờ. Clip vẫn lệch → xem lại khung thật, đổi/bỏ clip,
  hoặc nói thẳng cần chỉnh màu tay (CapCut/DaVinci). Không hứa "đồng màu".
- **Phụ đề không phải toàn bộ thiết kế hình ảnh.** Phụ đề = chuyển lời nói thành chữ dễ đọc. Hình (chọn cảnh, bố cục, nhịp),
  tiêu đề, âm thanh và màu quyết định cảm xúc. Đừng dùng karaoke/chữ to để bù cho footage yếu.
- **Tiêu đề ≠ caption.** Tiêu đề: ngắn, 1 ý, ở lúc mở hoặc đổi chương, có thể đậm hơn/màu nhấn. Caption: bám lời nói/lời đọc,
  đồng nhất style suốt video, thứ yếu so với hình. Hai thứ không dùng chung vị trí và không xuất hiện cùng lúc che nhau.
- **Nhịp có lý do.** Cắt khi có chuyển ý, đổi chủ thể, hoặc theo beat nhạc **nếu** concept cần. Nếu người dùng yêu cầu rõ "mỗi
  cảnh 3 giây" hoặc "30 s = 10 × 3 s" thì tôn trọng (`--seconds 3`, xem Bước 4); nếu không, **3 s không phải mặc định chung** —
  mỗi concept bên dưới chỉ là khoảng thử.
- **Vùng trên khung 9:16 (soát bằng mắt, không tự động).** Hình chữ nhật `x 200–880, y 288–1248` trên 1080x1920 (viền hồng trong
  contact sheet) là **ranh giới xem trước CHỮ do engine dùng, mang tính thận trọng** — không phải ranh giới chung cho mọi nền
  tảng/định dạng organic hay quảng cáo, và **không phải ranh giới của chủ thể**. Chủ thể, cảnh và khoảng trống âm (negative
  space) được phép nằm ngoài viền; khoảng trống không tự động là "vùng chết". Chỉ cần tránh để **chữ** nằm ngoài viền. Trong
  viền, phân vai theo mục đích: *vùng tiêu đề* (phần trên), *vùng caption* (phần dưới của viền, nâng nhẹ để khỏi sát đáy; BBC
  ghi video 9:16 thường đặt phụ đề cao hơn một chút vì mặt hay nằm nửa trên), *vùng chủ thể chính* và *vùng mắt/mặt* — hai
  vùng này **do bạn nhìn khung thật rồi xác định**. Công cụ **không** dò chủ thể để tự đặt chữ (trừ `ags_reframe.py` bám mặt cho
  clip có mặt người). Chữ không che mặt, miệng, vật thể bán, số liệu có trong hình; nếu cần chắc chắn với một nền tảng cụ thể,
  kiểm tra lại hướng dẫn hiện hành của nền tảng đó.
- **Chữ & màu.** Weight/phông dưới đây là gợi ý; engine hiện dùng phông hệ thống (Arial Bold cho `clean`/`karaoke`, Georgia cho
  `editorial`) và **không đóng gói phông**. Phông khác chỉ dùng khi đã cài trên máy và đã kiểm tra dấu tiếng Việt hiển thị đúng
  trong khung thật. Độ tương phản chữ–nền: mục tiêu tối thiểu 4.5:1 (chữ lớn 3:1) theo WCAG 1.4.3; chữ trắng trên nền sáng/lộn
  xộn thì thêm viền/bóng, không chỉ tin màu.

## 1. Quy trình bắt buộc cho mọi concept
1. **Chọn concept + viết cảm xúc đích** (1 câu) và nói lại cho người dùng ở đầu bàn giao.
2. **Storyboard trước khi render (bắt buộc).** Xem từng clip nguồn (khung đầu/giữa/cuối), rồi lập bảng sau và lưu cạnh `out/`
   (ví dụ `out/storyboard.md`). Chưa có bảng → chưa chạy `render`:

   | # | File nguồn | Mục đích cảnh (vì sao ở đây) | Chủ thể & vị trí trong khung | Thời lượng & lý do | Nối sang cảnh sau (cut/dissolve/wipe, vì sao) | Tiêu đề (nếu có) | Caption (nếu có) |
   |---|---|---|---|---|---|---|---|

   Mỗi hàng phải trả lời được "bỏ cảnh này thì câu chuyện mất gì?". Không trả lời được → bỏ cảnh. Cột "chủ thể & vị trí" ghi
   những gì **bạn thấy** trong khung (ví dụ "người ở 1/3 trái, mắt ~y 700") — không suy từ tên file.
3. **Render**, rồi **soát khung thật tại mối nối.** `render` in `cut_times`; với mỗi mốc `t` lấy khung trước/sau
   (`ffmpeg -ss <t-0.2> -i video.mp4 -frames:v 1 out/join_a.jpg`, tương tự `t+0.2`) và **xem ảnh**. Contact sheet của guard chỉ lấy
   mẫu đều theo thời gian, **không bảo đảm** rơi vào mối nối — không thay được bước này. Kiểm: chủ thể bị cắt mất phần quan trọng
   hoặc nhảy vị trí giữa hai cảnh? chữ nằm ngoài viền xem trước chữ? nhảy màu/độ sáng giữa hai clip? chữ che mặt/vật? caption đè tiêu đề? lỗi dấu tiếng Việt?
4. Sửa storyboard/tham số → render lại → soát lại. Bàn giao kèm concept đã chọn, storyboard và những gì **chưa** làm được
   tự động (chỉnh màu tay, nhịp theo cảm xúc cần người nghe).

## 2. Năm concept

### 2.1 Calm travel (du lịch êm)
- **Cảm xúc đích:** thư giãn, muốn đến đó; cảm giác thở chậm.
- **Chọn cảnh & mạch:** mở bằng một cảnh rộng định vị nơi chốn → chi tiết (nước, ánh sáng, tay, vật liệu) → cảnh có người nhỏ
  trong không gian lớn → cảnh kết lắng. Ưu tiên chuyển động chậm, một hướng; tránh xen cảnh rung/nhanh.
- **Nhịp có lý do:** cảnh dài hơn để người xem "ở lại"; thử ~4–6 s/cảnh cho cảnh rộng, ngắn hơn cho chi tiết. Chuyển chủ yếu
  `dissolve` (0.5 s) hoặc `cut` khi cùng hướng chuyển động. Nếu người dùng bắt 3 s/cảnh thì giữ 3 s và dùng `dissolve` để bớt gắt.
  Ví dụ lệnh thử: `--seconds 5 --transition dissolve --zoom none --grade warm`.
- **Tiêu đề vs caption:** tiêu đề địa điểm ngắn, mở đầu, weight vừa–đậm, chữ trắng/kem, nhỏ hơn thường lệ, đặt vùng trên. Caption
  chỉ khi có lời đọc; style `clean`, ít chữ mỗi cụm; hoặc không caption nếu không có lời.
- **Màu:** `--grade warm` hoặc `natural` nhẹ; không đẩy bão hoà.
- **Âm thanh:** nhạc nền mềm, lời đọc (nếu có) chậm; nhạc tự nhỏ khi có giọng (`--voice`). SFX gần như không dùng, hoặc rất nhỏ ở chuyển chương.
- **Tránh:** cắt dồn dập; chữ to che cảnh đẹp; zoom thấy rõ; chuyển wipe; chữ màu chói.
- **Checklist soát khung:** chủ thể/đường chân trời không bị cắt; không có cảnh lệch tông rõ; chữ không che điểm nhìn chính;
  khung cuối có "điểm dừng" thay vì cắt đột ngột.

### 2.2 Cinematic narrative (kể chuyện điện ảnh)
- **Cảm xúc đích:** tò mò rồi cảm giác có mạch; xem tới cuối để biết kết.
- **Chọn cảnh & mạch:** có tình huống/câu hỏi ở đầu → leo thang bằng cảnh gần hơn/chi tiết hơn → một cảnh "đổi" (khám phá,
  tương phản) → kết. Xen cảnh rộng và gần có chủ đích; cảnh nối nhau phải khác cỡ cảnh hoặc góc rõ ràng, tránh hai cảnh gần giống.
  Bố cục: để chủ thể nằm lệch có chủ đích khi có chỗ "nhìn vào"; xác nhận bằng khung thật, không theo công thức cứng (video
  Every Frame a Painting về phim *Drive* chỉ được dùng ở mức mô tả công khai của video, xem nguồn 5 — không phải kết luận từ nội dung video).
- **Nhịp có lý do:** cảnh đổi/khám phá được giữ lâu hơn; đoạn leo thang ngắn dần **nếu hình tiếp theo mang thông tin mới**.
  Thử `--transition cut` là chính, `dissolve` cho chuyển thời gian/địa điểm.
- **Tiêu đề vs caption:** tiêu đề kiểu "chương" rất ít, weight đậm vừa, có thể serif (`--style editorial` cho caption Georgia);
  caption thấp hơn, dễ đọc, một sắc.
- **Màu:** `--grade natural`; đừng gán màu theo "mood" bằng cách đẩy mạnh — nếu cần tông điện ảnh thật sự thì nói cần chỉnh tay.
- **Âm thanh:** nhạc có chuyển động theo mạch truyện; khoảng lặng ngắn trước cảnh "đổi" cũng là lựa chọn; SFX tiết chế (chuyển cảnh/nhấn).
- **Tránh:** mở bằng logo/CTA; cắt nhanh liên tục không có thông tin mới; chữ lớn đè khung đã bố cục.
- **Checklist soát khung:** mỗi mối nối có lý do (đổi cỡ cảnh/góc/ý); mắt/mặt nhân vật không bị chữ che; cảnh "đổi" thực sự khác cảnh
  trước; không có hai cảnh liền nhau na ná.

### 2.3 Energetic social (năng lượng cao)
- **Cảm xúc đích:** hứng khởi, bắt kịp nhịp; muốn xem tiếp vài giây nữa.
- **Chọn cảnh & mạch:** mở bằng cảnh mạnh nhất (kết quả/khoảnh khắc ấn tượng) → gom các cảnh theo ý chính → kết bằng một hành động
  rõ. Mỗi cảnh phải có hành động hoặc thông tin mới.
- **Nhịp có lý do:** cắt khớp beat (`--auto-beat --beat-step 2` hoặc `4`) hoặc theo từng ý lời đọc; thử ~1.5–3 s/cảnh.
  Nếu người dùng yêu cầu 3 s/cảnh thì dùng đúng 3 s. Dài hơn người xem thấy vẫn cần cảnh mới nếu hành động đã hết.
  Thử: `--transition cut --zoom subtle --grade natural`.
- **Tiêu đề vs caption:** tiêu đề/hook ngắn, đậm, tương phản cao, ở vùng trên trong vùng an toàn, mất sau cụm đầu. Caption karaoke
  hoặc `clean` đậm (`--style karaoke --keywords "..."`), tô màu **một vài từ khoá thật sự quan trọng**, không tô cả câu; ≤ 3
  dòng (BBC khuyến nghị tối đa 3 dòng cho 9:16 — tham chiếu dễ đọc, không phải luật mạng xã hội).
- **Màu:** `--grade natural`; màu nhấn dùng cho một loại thông tin, không đổi tuỳ hứng.
- **Âm thanh:** nhạc có nhịp rõ, SFX nhỏ ở các chuyển ý quan trọng (`ags_sfx.py`, gain thấp); giọng luôn nghe rõ trên nhạc.
- **Tránh:** SFX ở mọi mối nối; zoom + wipe + karaoke cùng lúc; hook hứa điều video không có; caption che mặt nói.
- **Checklist soát khung:** hook đọc được trong 1 lần nhìn; mặt/miệng không bị che; từ tô màu là từ khoá, không phải cả cụm;
  không nhiều hơn một "hiệu ứng nổi" trong cùng một cảnh; mối nối không có khung rác/nhảy chủ thể.

### 2.4 Clean product (sản phẩm sạch)
- **Cảm xúc đích:** tin cậy, rõ ràng, "tôi hiểu sản phẩm/bất động sản này".
- **Chọn cảnh & mạch:** tổng thể → điểm khác biệt/tính năng chính (mỗi cảnh một ý) → bằng chứng thực (không bịa số liệu, giá,
  pháp lý — xem Bước 1) → CTA. Cảnh sạch, ổn định, ánh sáng đều.
- **Nhịp có lý do:** đủ lâu để đọc/ nhìn rõ chi tiết cần xem; thử ~3–5 s/cảnh (3 s hợp lý nếu người dùng yêu cầu). Chuyển `cut` hoặc
  `dissolve` ngắn; `--zoom subtle` chỉ khi không làm lệch vật cần nhìn.
- **Tiêu đề vs caption:** tiêu đề tên + 1 điểm chính, đậm, rõ; số liệu (giá, diện tích) là chữ do bạn kiểm chứng từ người dùng,
  đặt trong vùng an toàn. Caption `clean` đồng nhất. Sans-serif trung tính (Arial Bold của engine; nếu cài thêm, Noto Sans/Inter —
  xem nguồn); màu thương hiệu nếu có, một màu nhấn.
- **Màu:** `--grade natural`; ưu tiên màu thật của sản phẩm — không dùng `warm` làm sai màu vật liệu/sơn.
- **Âm thanh:** nhạc nhẹ nền, giọng đọc rõ, SFX hầu như không.
- **Tránh:** nhiều hiệu ứng chuyển; chữ che vật; số liệu không có nguồn; clip sản phẩm lệch màu rõ đặt cạnh nhau.
- **Checklist soát khung:** vật/mặt tiền không bị cắt; chữ không che chi tiết bán hàng; màu sản phẩm đúng thực tế; chữ/số trong ảnh
  khớp dữ liệu người dùng đưa; CTA nằm trong vùng an toàn.

### 2.5 Personal documentary (tài liệu cá nhân)
- **Cảm xúc đích:** gần gũi, chân thật; người xem tin người kể.
- **Chọn cảnh & mạch:** mở bằng khoảnh khắc đời thường hoặc câu nói thật → bối cảnh → thay đổi/khó khăn → hiện tại/kết. Giữ cảnh
  "chưa đẹp" nhưng thật; B-roll phục vụ lời kể, không thay lời kể.
- **Nhịp có lý do:** theo hơi thở của lời nói/lời đọc; thử ~3–6 s, cho phép cảnh dài khi cảm xúc cần. Chuyển `cut` hoặc `dissolve`
  khi đổi thời điểm. Nếu người dùng bắt 3 s thì giữ 3 s nhưng chọn cảnh có hành động ngắn gọn.
- **Tiêu đề vs caption:** tiêu đề nhỏ, thưa (tên/địa điểm/năm do người dùng cung cấp). Caption là phần quan trọng ở đây: `clean` hoặc
  `editorial`, chữ trắng, nền/viền đủ tương phản, đặt không che mặt người kể; sai chính tả là lỗi nặng — dùng `--script` với lời đã duyệt.
- **Màu:** `--grade none` hoặc `natural`; không ép màu thẩm mỹ lên da người thật; clip lệch màu thì ghi chú cần chỉnh tay.
- **Âm thanh:** giữ tiếng thật khi có (lưu ý `render` mặc định **bỏ tiếng gốc** của clip — nếu tiếng gốc là nội dung chính thì
  không dùng `render` cho cảnh đó và nói rõ giới hạn với người dùng (đừng bịa); nhạc rất nhẹ, ít SFX.
- **Tránh:** làm bóng bẩy quá mức; nhạc cảm xúc "đẩy" thay cho nội dung; hiệu ứng zoom/wipe làm mất tính thật; chữ che mặt người kể.
- **Checklist soát khung:** mặt và mắt người kể rõ, không bị chữ che; da không lệch màu rõ giữa các clip; caption đúng chính tả và đúng lời;
  mối nối không cắt giữa câu/ cử chỉ.

## 3. Tham số recipe = heuristic (nói rõ khi bàn giao)
| Tham số | Dùng để | Giới hạn thật |
|---|---|---|
| `--seconds` / `--beat-step` | độ dài mỗi cảnh | khoảng thử trong từng concept; người dùng chỉ định thì theo người dùng |
| `--transition` (`cut`, `dissolve`, `wipe`) | cách nối | không biết cảnh có "nên" nối kiểu đó — bạn xem khung thật |
| `--zoom` (`none`, `subtle`, `auto`) | chuyển động nhẹ | không tránh được cắt mất chủ thể ở mép: soát khung |
| `--grade` (`none`, `natural`, `warm`) | công thức giống nhau cho mọi clip | **không** khớp màu giữa nguồn |
| `--style` (`clean`, `karaoke`, `editorial`) + `--keywords` | kiểu phụ đề | chỉ chữ; không thay thiết kế hình |
| `ags_sfx.py` gain thấp | nhấn chuyển ý | dễ lạm dụng — ít hơn là tốt |

## 4. Nguồn tham chiếu (đã mở được ngày 2026-10-08)
Không nguồn nào chứng minh một concept gây ra view/viral; chúng chỉ làm căn cứ cho khả năng đọc, giấy phép phông và cách nhìn bố cục.
1. BBC — *Subtitle Guidelines*: https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles — đã đọc mục 3.3 (video 9:16 tối đa 3 dòng),
   4.2.1 (shot changes), 8.1 (trắng trên đen cho dễ đọc), 10.1 (9:16 thường đặt phụ đề cao hơn một chút, mặt thường ở nửa trên). Là chuẩn
   phát sóng/online của BBC, dùng làm baseline dễ đọc, **không** phải quy định của TikTok/Reels/Shorts.
2. W3C — *WCAG 2.2*, tiêu chí 1.4.3 Contrast (Minimum): https://www.w3.org/TR/WCAG22/ — đã đọc: chữ ≥ 4.5:1, chữ lớn ≥ 3:1.
3. Inter (rsms): https://github.com/rsms/inter — đã đọc README: giấy phép SIL OFL 1.1, bảng weight 100–900. README không nêu hỗ trợ tiếng Việt → tự kiểm dấu.
4. Noto Sans (Google Fonts repo): https://github.com/google/fonts/tree/main/ofl/notosans — đã đọc `METADATA.pb`/`OFL.txt`: OFL, trục weight 100–900,
   subset `vietnamese`.
5. Every Frame a Painting — "Drive (2011) - The Quadrant System": https://www.youtube.com/watch?v=wsI8UES59TM — **chỉ đã xác nhận tiêu đề, kênh, độ dài 3:34 và
   phần mô tả (nói rằng hình ảnh trong phim chủ yếu theo một "quadrant system", kèm các chi tiết tinh tế trong khung)**. **Transcript không có; video không được xem/nghe**
   khi soạn tài liệu này → không trích lời, mốc thời gian, hay kết luận về nội dung video; chỉ là gợi ý để tự soát bố cục.
6. Hayden Hillier-Smith — trang bán khoá học công khai: https://hayden-hillier-smith.mykajabi.com/ — chỉ đọc **mô tả của trang bán khoá học** (tác giả
   tự nêu kinh nghiệm dựng cho nhiều creator và quan điểm dựng vì cảm xúc thay vì chỉ "retention"). **Không truy cập nội dung khoá học**; đây là quan điểm của
   người bán, không phải bằng chứng đo lường hay căn cứ nhân quả cho hiệu quả của cách dựng nào.

Phân biệt: mục 1–4 là văn bản kỹ thuật đã đọc trực tiếp; mục 5 chỉ có mô tả video (không xem); mục 6 chỉ có mô tả trang bán khoá học (không truy cập khoá).
