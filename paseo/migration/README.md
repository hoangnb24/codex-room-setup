# Khảo sát ban đầu: fork và upstream — 2026-09-15

> Tài liệu này ghi lại khảo sát trước khi triển khai. Cấu hình và quy trình hiện hành
> đã chuyển sang **stable v0.8.0**, không dùng đầu nhánh main được khảo sát dưới đây.
> Xem [hướng dẫn release hiện hành](../../docs/paseo-release.md).

## Kết luận

Có thể thay phần mở rộng MCP theo provider của fork bằng tính năng chính thức `agents.providers.<id>.paseoTools`. Không cần liệt kê từng tool bị cấm để giữ cách chia vai hiện tại: dùng `enabled: false` cho mọi provider ngoài Supervisor và Lead.

Đây là kết quả khảo sát và config ứng viên; chưa đổi origin, checkout, bộ cài, config đang chạy hoặc restart daemon.

## Các bản đã đối chiếu

- Checkout `~/projects/supervisors/paseo`: nhánh `main`, origin là `git@github.com:hoangnb24/paseo.git`, upstream là `git@github.com:getpaseo/paseo.git`.
- HEAD và origin/main sau fetch: `8511089eaeb06cddd049b629562926822020de5c`, ngày 2026-08-28, describe `v0.7.0-beta.1-13-g8511089ea`. Trùng pin trong `paseo/source.toml`.
- upstream/main sau fetch: `cb90806045eb636a176c46b30b9e16cb5fa0a120`, describe `v0.8.0-34-gcb9080604`, package version `0.8.0`.
- Hai nhánh đã rẽ: fork có 12 commit riêng (gồm merge/commit lặp lại), upstream có 193 commit riêng. Không thể chuyển bằng fast-forward từ HEAD hiện tại.
- Fetch tags gặp tag cũ `v0.4.0-beta.2` khác nội dung local; không ghi đè tag đó. Fetch upstream/main riêng với `--no-tags` sau đó thành công.
- `~/.paseo/config.json` khớp hoàn toàn với template hiện tại sau thay `@@HOME@@`.

## Config cần đổi

1. Giữ `daemon.mcp.enabled: true` và `daemon.mcp.injectIntoAgents: true`.
2. Xóa `daemon.mcp.injectIntoProviders` (trường riêng của fork). Upstream không dùng trường này để chặn tool; schema cho phép trường lạ nên bỏ sót có thể không báo lỗi.
3. Thêm `paseoTools: { "enabled": true }` vào `codex-supervisor` và `codex-lead`.
4. Thêm `paseoTools: { "enabled": false }` vào `codex-peer` và mọi provider khác để giữ phạm vi cũ.

Config đầy đủ: [template hiện hành](../../home/.paseo/config.json.template). Bản này được tạo từ template đang chỉnh sửa của người dùng, giữ nguyên model, thinking, command, params và các thiết lập còn lại; chỉ chuyển chính sách MCP. Đã khai báo tắt cả các provider dựng sẵn `claude`, `codex`, `copilot`, `opencode`, `pi`, `omp` và các provider tùy chỉnh `grok`, `hermes`.

### Khác biệt hành vi quan trọng

- Upstream mặc định bật đầy đủ tool khi provider không có `paseoTools`. Fork dùng allowlist nên provider mới mặc định nằm ngoài danh sách. Khi thêm provider sau này, cần đặt chính sách rõ ràng; upstream hiện không có default-deny toàn cục tương đương allowlist cũ.
- `extends: "codex"` không kế thừa chính sách tool. Mỗi ID provider có chính sách riêng.
- `paseoTools.enabled` chỉ điều khiển bộ tool của Paseo; `providers.<id>.enabled` điều khiển chính provider. Không thay thế hai trường này cho nhau.
- `paseoTools.disabledTools` chỉ cần nếu muốn giữ một phần bộ tool; dùng đúng ID tool. Không nhầm với `disallowedTools` của provider runtime.
- Upstream áp dụng chính sách cho cả MCP và native tools. Voice `speak` được xử lý riêng; cấu hình hiện tại đã tắt voice.
- Sau chuyển bản chạy: reload config rồi tạo agent mới hoặc reload agent cũ. Phiên đang chạy giữ bộ tool nhận lúc khởi động.
- Các trường `extends`, `command`, `env`, `params`, `models`, `additionalModels`, `thinkingOptions` và `isDefault` vẫn có trong schema upstream; không thấy yêu cầu đổi các profile hiện tại ở tầng config.

## Phần Room setup cần sửa cùng lúc

Chỉ đổi remote URL và JSON chưa đủ:

| Thành phần | Điều chỉnh cần làm |
| --- | --- |
| `paseo/source.toml` | Đổi nguồn chính sang getpaseo, cập nhật commit/version đã kiểm tra |
| `scripts/install-paseo-fork` | Hỗ trợ nguồn upstream và chuyển checkout đã rẽ nhánh; hiện chỉ nhận no-op hoặc fast-forward, kiểm tra đúng topology fork |
| `scripts/install-room` | Đồng bộ kiểm tra remote/provenance và quy trình chuyển checkout/rollback |
| `home/.local/bin/paseo-local-update` | Bỏ URL fork và pin cũ hardcode; sửa kiểm tra nguồn, topology, cách chọn bản cập nhật |
| `scripts/verify`, `scripts/doctor` | Kiểm tra nguồn upstream và chính sách `paseoTools` |
| `scripts/export-current` | Thay điều kiện allowlist cũ bằng chính sách provider mới |
| `tests/test_setup.py`, `tests/container/accept`, các test liên quan | Sửa kỳ vọng về nguồn, pin, migration và MCP |
| README và `paseo/notes/*`, `docs/paseo-fork.md` | Cập nhật hướng dẫn và hành vi thực tế |

Khuyến nghị bỏ fork nhưng vẫn pin một bản upstream đã kiểm tra. Updater nên có bước chủ động chọn bản upstream mới và kiểm tra build trước khi cập nhật pin. Bộ hiện tại yêu cầu branch tip đúng bằng pin, nên pin một lần vẫn chưa giải quyết mong muốn cập nhật thuận tiện khi main tiếp tục tiến lên.

Chuyển lần đầu nên giữ checkout fork làm bản quay lại, build upstream trong checkout riêng rồi chuyển bộ chạy sau kiểm tra. Không merge upstream vào fork để thực hiện migration này.

## Một thay đổi riêng khác của fork

Fork có patch `c81cb8473` cho phép client loopback thiếu bearer token kết nối ngay cả khi daemon có password. Upstream mới vẫn kiểm tra token khi có password (websocket-server.ts, attachAuthenticatedSocket); không giữ ngoại lệ đó. Config JSON đang đối chiếu không khai báo password, nhưng cần kiểm tra thiết lập thực tế qua môi trường/CLI và kết nối Desktop/CLI trước khi thay bộ chạy. Không kết luận tương thích kết nối chỉ từ việc schema MCP hợp lệ.

## Kiểm chứng đã thực hiện và giới hạn

- Fetch cả origin và upstream; đối chiếu HEAD, branch, version, lịch sử riêng và source upstream.
- Chạy schema `ProviderOverridesSchema` lấy trực tiếp từ upstream đã fetch với toàn bộ 11 provider trong config ứng viên: PASS.
- Chạy các hàm chính sách upstream với 11 provider: chỉ Supervisor/Lead được bật bộ tool và `create_agent`: PASS. Xác nhận provider chưa khai báo mặc định bật.
- Đọc đường khởi chạy agent xác nhận cùng gate áp dụng cho MCP/native, và test upstream về snapshot chính sách theo phiên.
- Chưa build toàn bộ upstream, chưa chạy daemon upstream, chưa kiểm tra migration dữ liệu hoặc kết nối Desktop/CLI. Kết luận ở mức config/source; chưa phải xác nhận thay bản chạy thành công.

## Nguồn upstream

- [Tính năng chính thức #4277, merge ngày 2026-09-03](https://github.com/getpaseo/paseo/commit/53c96074791089949f6917cfa55db1d11f212521)
- [Tài liệu MCP tại commit đã kiểm tra](https://github.com/getpaseo/paseo/blob/cb90806045eb636a176c46b30b9e16cb5fa0a120/public-docs/mcp.md)
- [Schema provider](https://github.com/getpaseo/paseo/blob/cb90806045eb636a176c46b30b9e16cb5fa0a120/packages/protocol/src/provider-config.ts)
- [Logic chọn chính sách theo ID provider](https://github.com/getpaseo/paseo/blob/cb90806045eb636a176c46b30b9e16cb5fa0a120/packages/server/src/server/agent/paseo-tool-policy.ts)
