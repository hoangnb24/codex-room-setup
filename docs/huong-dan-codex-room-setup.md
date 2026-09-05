# Hướng dẫn `codex-room-setup`

Tài liệu này giải thích cách bộ setup tạo một phòng Codex gồm ba vai trò và
cách các vai trò phối hợp để hoàn thành một outcome kỹ thuật.

## Bức tranh tổng thể

```text
Paseo provider
    -> ~/.local/bin/codex-room <role>
    -> codex-room-sync <role>
    -> ~/.codex-runtime/<role>/config.toml
    -> Codex với CODEX_HOME riêng
```

Ba provider là `codex-supervisor`, `codex-lead`, và `codex-peer`. Supervisor và
Lead nhận Paseo MCP; Peer không nhận MCP điều phối.

## Ranh giới trách nhiệm

- Human giữ mục tiêu sản phẩm, ưu tiên, chi phí vật chất, tác động bên ngoài,
  và quyết định rủi ro không thể đảo ngược.
- Supervisor quan sát workspace, chuyển nguyên vẹn chỉ thị của Human, và thực
  hiện phục hồi vận hành có giới hạn. Supervisor không trở thành Lead thứ hai.
- Lead giữ quyết định kỹ thuật của một dự án, dependency order, tích hợp,
  kiểm chứng, và quyết định chấp nhận candidate.
- Peer nhận đúng một outcome có giới hạn. Peer có thể triển khai, điều tra,
  đưa ra ý kiến kiến trúc, hoặc kiểm tra candidate trong phạm vi được giao.

Lead chỉ có tối đa một Peer đang ghi vào repository tại một thời điểm. Peer có
thể gửi `REOPEN_REQUEST` khi tiền đề kỹ thuật thất bại,
`DEPENDENCY_REQUEST` khi thiếu prerequisite chưa có owner, hoặc `BLOCKED` khi
không còn bước an toàn trong phạm vi. Mỗi tín hiệu cần nêu bằng chứng, hệ quả,
và quyết định cần có.

Khi một quyết định kiến trúc hoặc candidate có rủi ro đủ lớn, Lead có thể gọi
một Peer mới ở chế độ chỉ đọc để xem đúng candidate hoặc snapshot đã cố định.
Đây vẫn là Peer theo nhiệm vụ, không tạo thêm provider hay cấp bậc mới.

## Cài đặt và sinh runtime

Luồng public duy nhất là `./install` để xem kế hoạch, `./install --apply` để
cài đặt, sau đó operator khởi động Paseo và chạy `./install --verify`. Các
script thấp hơn chỉ dành cho bảo trì có mục tiêu, không phải một đường cài đặt
thay thế.

`home/` là bản mirror của `$HOME`. `./install --apply` cài overlay, chỉ
dẫn chung, workspace protocol, launcher, và cấu hình Paseo. Script không ghi
vào `~/.codex`.

`codex-room-sync` đọc `~/.codex/config.toml` làm base, áp dụng các scalar được
cho phép trong overlay, ghép chỉ dẫn của role, và sinh `config.toml` cùng model
catalog riêng. Nó luôn tắt native Codex agents để Paseo giữ topology ba vai
trò. Auth, skills và plugins được dùng qua symlink; `hooks.json` là tùy chọn
và chỉ được chia sẻ khi có sẵn. Session, log, state và database vẫn tách theo role.

Generator không cần thêm workflow asset để chạy. Nó không khởi tạo, xóa, hay
ghi đè notebook riêng, session, runtime directory, hoặc byte thuộc `~/.codex`
của operator. Những file cũ còn tồn tại được giữ nguyên nhưng không phải là
dependency của runtime mới.

## Luồng một candidate

Lead gửi cho Peer outcome quan sát được, dependency, write scope, invariant,
bằng chứng nghiệm thu, và điều kiện cần mở lại quyết định. Peer tự điều tra
trong phạm vi đó, chạy proof phù hợp, rồi trả immutable candidate (commit hoặc
snapshot), base ban đầu, danh sách path, lệnh đã chạy, và rủi ro còn lại.

Lead đọc artifact chính xác và đưa ra quyết định kỹ thuật rõ ràng: chấp nhận
hoặc từ chối, kèm lý do. Test pass, thông báo hoàn thành, và trạng thái
workspace là bằng chứng hỗ trợ; chúng không tự tạo thành acceptance.

Sau khi dispatch, các role chờ event finish, error, attention, hoặc decision.
Không lặp lại truy vấn khi state chưa đổi.

## Các lệnh thường dùng

```bash
# Xem kế hoạch đầy đủ, không ghi filesystem
./install

# Cài đặt đầy đủ với transaction/rollback
./install --apply

# Kiểm tra installed và live provider (daemon phải đang chạy)
./install --verify

# Kiểm tra source, không cần runtime đã cài
./scripts/verify --source

# Chạy test của repository
make test
```

Sau khi thay provider catalog trong `home/.paseo/config.json.template`, chạy
`make test`, `./scripts/verify --source`, `./install --apply`, restart Paseo,
rồi chạy `./install --verify` nếu daemon đang hoạt động. Kiểm tra live provider và
MCP là bước vận hành của operator, không được suy ra chỉ từ test source.

## Sửa ở đâu?

- Đổi model hoặc authority của role: sửa overlay tương ứng.
- Đổi provider, command, hoặc MCP boundary: sửa
  `home/.paseo/config.json.template`.
- Đổi cách ghép config: sửa `home/.local/bin/codex-room-sync` và test boundary
  tương ứng.
- Đổi nguyên tắc phối hợp chung: sửa
  `home/.config/codex-room/workflow/WORKSPACE_PROTOCOL.md`.

Không sửa trực tiếp `~/.codex-runtime/<role>/config.toml`; đó là output được
sinh lại. Không đưa auth, session, log, database, keypair, token, hay private
workspace state vào Git.
