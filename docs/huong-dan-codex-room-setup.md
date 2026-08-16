# Hiểu toàn bộ `codex-room-setup` từ gốc đến ngọn

Tài liệu này dành cho người mới tiếp cận `codex-room-setup`. Mục tiêu không chỉ là giúp bạn chạy được bộ công cụ, mà còn giúp bạn hiểu **thành phần nào chịu trách nhiệm cho việc gì**, một thay đổi đi qua hệ thống ra sao, và nên điều chỉnh ở đâu khi muốn áp dụng cho nhu cầu riêng.

## 1. Bức tranh ngắn gọn nhất

`codex-room-setup` tạo một “phòng làm việc” gồm bốn vai trò Codex:

| Vai trò | Trách nhiệm cốt lõi | Có công cụ điều phối Paseo |
| --- | --- | --- |
| Supervisor | Quan sát nhiều workspace, chuyển chỉ thị của chủ dự án, phát hiện vấn đề quy trình | Có |
| Lead | Chịu trách nhiệm kỹ thuật của một dự án: chia việc, tích hợp, kiểm chứng và ra quyết định | Có |
| Peer | Thực hiện hoặc điều tra một phạm vi cụ thể do Lead giao | Không |
| Review | Đọc và phản biện một candidate ổn định; không sửa code | Không |

Hãy hình dung hệ thống như sau:

```text
Người dùng chọn một provider trong Paseo
        |
        v
Paseo chạy: codex-room <role>
        |
        v
codex-room-sync ghép cấu hình gốc + overlay của role
        |
        v
~/.codex-runtime/<role>/config.toml
        |
        v
Codex chạy với CODEX_HOME riêng của role đó
```

Ví dụ, khi Paseo mở một Lead:

```text
codex-lead
  -> ~/.local/bin/codex-room lead
  -> ~/.local/bin/codex-room-sync lead
  -> tạo/cập nhật ~/.codex-runtime/lead
  -> CODEX_HOME=~/.codex-runtime/lead codex ...
```

Kết quả là Lead có model, chỉ dẫn và session riêng, nhưng vẫn dùng thông tin đăng nhập, skill và plugin Codex hiện có của người vận hành.

## 2. Ba ý cốt lõi cần nhớ

### 2.1 `~/.codex` vẫn thuộc quyền quản lý của người vận hành

`~/.codex` là vùng cá nhân do người vận hành và Codex quản lý. Nó chứa cấu hình gốc, đăng nhập, skill, plugin, hook và chỉ dẫn toàn cục.

`codex-room-setup` **đọc** `~/.codex/config.toml` để làm cấu hình nền và tạo symlink tới một số tài nguyên dùng chung. Bộ công cụ không cài file vào `~/.codex`.

Nguyên nhân và kết quả:

```text
Không đóng gói auth cùng cấu hình chia sẻ
  -> mỗi người tự đăng nhập Codex trên máy của mình
  -> bộ setup có thể chia sẻ mà không chia sẻ token
  -> đổi mật khẩu hoặc cập nhật skill ở ~/.codex có hiệu lực qua symlink
```

### 2.2 Mỗi role có một `CODEX_HOME` riêng

Bốn thư mục runtime dự kiến là:

```text
~/.codex-runtime/supervisor
~/.codex-runtime/lead
~/.codex-runtime/peer
~/.codex-runtime/review
```

Các role dùng chung danh tính và tài nguyên ổn định, nhưng tách state có thể thay đổi:

| Dùng chung qua symlink | Tách riêng theo role |
| --- | --- |
| `auth.json` | `config.toml` |
| `AGENTS.md` | `sessions/` |
| `hooks.json` | log, memory, queue |
| `skills/` | SQLite và state runtime |
| `plugins/` | model catalog đã xử lý |

Nhờ vậy, một session Review không trộn vào lịch sử của Lead, nhưng cả hai vẫn dùng cùng tài khoản Codex.

### 2.3 Paseo sở hữu topology; native Codex agents bị tắt

Paseo quyết định ai là Supervisor, Lead, Peer và Review. Vì vậy bộ setup chủ động:

- đặt `[agents].enabled = false`;
- đặt `multi_agent = false` và `multi_agent_v2 = false`;
- xóa `multi_agent_version` khỏi catalog model được sinh.

Nếu không làm vậy, có thể tồn tại hai lớp điều phối song song: Paseo điều phối bốn role, trong khi Codex lại tự tạo native agents bên trong từng role. Hậu quả là ownership và luồng giao việc trở nên khó kiểm soát.

## 3. Bốn loại file: biết loại trước khi sửa

| Loại | Ví dụ | Có nên sửa trực tiếp? |
| --- | --- | --- |
| Mẫu cấu hình gốc | `home/.config/codex-room/overlays/lead.config.toml` | Có |
| File đã cài trong HOME | `~/.config/codex-room/overlays/lead.config.toml` | Chỉ sửa tạm; nên đưa thay đổi về mẫu gốc |
| Runtime được sinh | `~/.codex-runtime/lead/config.toml` | Không |
| State riêng tư | auth, session, log, database, keypair | Không đóng gói hoặc chia sẻ |

Luồng thay đổi thực tế:

```text
Muốn đổi hành vi lâu dài
  -> sửa file mẫu trong bộ cấu hình
  -> cập nhật bản được cài trong HOME
  -> sinh lại runtime của role
```

Nếu bạn sửa thẳng `~/.codex-runtime/lead/config.toml`, lần sync kế tiếp sẽ sinh lại file và có thể làm mất thay đổi.

## 4. Cấu trúc bộ `codex-room-setup`

```text
codex-room-setup/
└── home/
    ├── .config/codex-room/
    │   ├── model-instructions.md    Chỉ dẫn chung cho Codex
    │   ├── overlays/                Cấu hình riêng của bốn role
    │   └── workflow/                Luật phối hợp giữa các role
    ├── .local/bin/
    │   ├── codex-room               Launcher chọn role
    │   └── codex-room-sync          Bộ sinh runtime
    └── .paseo/
        └── config.json.template     Catalog provider và ranh giới MCP
```

Các phần sau giải thích lần lượt từng nhóm.

## 5. `home/`: bản mẫu của HOME người dùng

Thư mục `home/` là một “HOME thu nhỏ”. Ví dụ:

```text
home/.local/bin/codex-room
  -> được đặt tại
~/.local/bin/codex-room
```

Mỗi file mẫu có một đường dẫn đích và permission xác định. Nhờ vậy, phần cấu hình chung, executable và file nhạy cảm có thể được quản lý với quyền truy cập khác nhau.

### 5.1 `model-instructions.md`: cách Codex cộng tác và giao tiếp

File này chứa chỉ dẫn chung về tính cách, cách viết, cách cập nhật tiến độ, thao tác file, tính tự chủ và an toàn. Nó trả lời câu hỏi: **mọi role nên làm việc với người dùng theo phong cách nền nào?**

Khi sync, file được nối vào từng runtime:

```text
~/.codex-runtime/<role>/model-instructions.md
  -> ~/.config/codex-room/model-instructions.md
```

Ứng dụng phù hợp:

- Muốn mọi role trả lời ngắn hơn: chỉnh quy tắc viết tại đây.
- Muốn chỉ Review thay đổi cách báo cáo finding: chỉnh overlay của Review, không chỉnh file chung này.
- Muốn thêm quy tắc riêng cho một dự án: dùng `AGENTS.md` của dự án đó thay vì làm file chung phình to.

### 5.2 `overlays/*.config.toml`: tính cách và mặc định riêng của từng role

Overlay là một mảnh cấu hình nhỏ được ghép lên `~/.codex/config.toml`. Nó không phải một config Codex hoàn chỉnh.

Các scalar hiện được phép override là:

```text
model
model_instructions_file
model_reasoning_effort
sandbox_mode
approval_policy
approvals_reviewer
```

Ngoài ra, mỗi overlay có `developer_instructions` mô tả trách nhiệm của role.

#### Supervisor overlay

Supervisor là lớp quản trị và quan sát, không phải Lead thứ hai. Nó theo dõi topology, chuyển đúng chỉ thị của chủ dự án và góp ý cho Lead khi có bằng chứng về vấn đề quy trình.

Ví dụ đúng: phát hiện hai Peer cùng sửa một subsystem và nhắc Lead thu hẹp ownership.

Ví dụ sai: tự vào workspace dự án sửa implementation chỉ vì thấy Lead làm chậm.

Supervisor còn có `SUPERVISOR_NOTEBOOK.md` riêng trong runtime để giữ bài học dài hạn. File này được **copy một lần khi chưa tồn tại**, không symlink, nên các ghi chép runtime không sửa ngược template gốc.

#### Lead overlay

Lead là thẩm quyền kỹ thuật của một dự án. Lead định nghĩa outcome, chia phạm vi, giữ dependency order, tích hợp, kiểm chứng và quyết định candidate có đạt hay không.

Một quy tắc quan trọng là “một moving write scope chỉ có một owner”. Ví dụ:

```text
Peer A sửa module thanh toán
Peer B đồng thời sửa chính module thanh toán
  -> phạm vi va chạm
  -> diff và bằng chứng của hai người không còn độc lập
```

Cách phù hợp là tách hai phạm vi thực sự độc lập hoặc cho một Peer sở hữu toàn bộ thay đổi dọc đó.

#### Peer overlay

Peer là cộng tác viên kỹ thuật cho một outcome bị giới hạn. Peer có thể tạm thời làm implementer, architect, scout hoặc reviewer; đó là trách nhiệm theo nhiệm vụ, không phải thêm role cố định.

Peer được phép phản hồi ba tín hiệu quan trọng:

- `REOPEN_REQUEST`: tiền đề kỹ thuật đã sai, cần mở lại quyết định.
- `DEPENDENCY_REQUEST`: thiếu một prerequisite chưa có owner.
- `BLOCKED`: không còn bước an toàn nào trong phạm vi hiện tại.

Ví dụ, Lead giao “thêm cache vào adapter X”, nhưng Peer chứng minh dữ liệu sai do source-of-truth có hai owner. Peer nên trả `REOPEN_REQUEST` kèm bằng chứng thay vì thêm cache để che triệu chứng.

#### Review overlay

Review là profile đọc và phản biện một candidate cố định. Mặc định dùng `gpt-5.6-luna` với reasoning `max`.

Review phải:

- xác nhận chính xác commit hoặc snapshot đang review;
- dừng với `STALE_CANDIDATE` nếu candidate đổi giữa chừng;
- hạch toán 100% file trong candidate;
- đưa finding theo dạng bằng chứng → hậu quả → cách bác bỏ → sửa nhỏ nhất;
- không sửa code và không tự ra phán quyết `ACCEPT`/`REVISE`.

Review còn bị xóa toàn bộ bảng `mcp_servers` kế thừa từ config gốc. Đây là phòng vệ thứ hai ngoài việc Paseo không inject MCP vào provider Review.

### 5.3 `workflow/`: luật phối hợp giữa các role

Ba file trong thư mục này có mục đích khác nhau:

#### `WORKSPACE_PROTOCOL.md`

Đây là “hiến pháp ngắn” của room. Nó định nghĩa:

- Human quyết định mục tiêu sản phẩm, chi phí, tác động bên ngoài và trade-off rủi ro;
- Supervisor quản trị portfolio và workflow;
- Lead quyết định kỹ thuật;
- Peer sở hữu outcome được giao;
- ai viết, ai review, ai chấp nhận.

Cause–effect tiêu biểu:

```text
Writer chứng minh thay đổi của mình
  -> Reviewer độc lập cố gắng bác bỏ candidate ổn định
  -> Lead xem artifact và toàn bộ bằng chứng
  -> Lead mới ra quyết định kỹ thuật
```

#### `ANTI_PATTERNS.md`

Đây là catalog các lỗi phối hợp thường gặp như pre-solving, hai writer va chạm, review candidate đang đổi, lấy “tests pass” làm acceptance, hoặc tạo quá nhiều ceremony.

File không biến một nghi ngờ thành mệnh lệnh. Nó yêu cầu lập finding packet có observation, evidence, counterevidence, risk và open question. Điều đó giúp hệ thống phản ứng dựa trên bằng chứng thay vì dựa trên role “cấp cao hơn”.

#### `SUPERVISOR_NOTEBOOK.md`

Đây là template cho sổ tay học hỏi dài hạn của Supervisor. Chỉ những pattern mới hoặc bằng chứng mạnh hơn mới nên được ghi. Mục đích là nhận ra lỗi lặp lại giữa nhiều workspace, không phải lưu log trạng thái hàng ngày.

### 5.4 `.paseo/config.json.template`: catalog provider và ranh giới MCP

File này nói cho Paseo biết có bốn provider Codex tùy biến. Mỗi provider có:

- tên và mô tả hiển thị;
- command, ví dụ `codex-room lead`;
- tham số sandbox/approval;
- danh sách model và reasoning option.

`@@HOME@@` là placeholder. Khi cài, nó được thay bằng HOME thật của người dùng. Ví dụ:

```text
@@HOME@@/.local/bin/codex-room
  -> /Users/alice/.local/bin/codex-room
```

File còn giới hạn Paseo MCP injection cho:

```json
["codex-supervisor", "codex-lead"]
```

Lý do: Supervisor và Lead cần nhìn/điều phối workspace; Peer chỉ cần làm scope được giao; Review cần bề mặt công cụ nhỏ và độc lập hơn.

Một điểm dễ sai là model tồn tại ở **hai nơi**:

1. Paseo provider catalog quyết định model hiển thị/chọn trong Paseo.
2. Role overlay quyết định model mặc định của tiến trình Codex sau sync.

Đổi một nơi mà quên nơi kia có thể khiến giao diện nói một model nhưng runtime mặc định lại là model khác.

## 6. Hai chương trình trung tâm: `codex-room` và `codex-room-sync`

### 6.1 `codex-room`: launcher mỏng

Launcher thực hiện đúng ba việc:

1. Nhận role từ đối số đầu tiên.
2. Gọi `codex-room-sync <role>` để runtime luôn mới.
3. đặt `CODEX_HOME` rồi `exec codex` với các đối số còn lại.

Ví dụ:

```bash
codex-room peer app-server
```

Sẽ tương đương về ý nghĩa với:

```text
sync peer
CODEX_HOME=~/.codex-runtime/peer
codex app-server
```

Việc sync ngay trước khi chạy giúp thay đổi trong overlay đang hoạt động được phản ánh vào runtime trước khi Codex khởi động.

### 6.2 `codex-room-sync`: máy sinh runtime

Đây là thành phần quan trọng nhất. Với mỗi role, nó làm theo thứ tự:

1. Xác định đường dẫn config gốc, overlay, workflow và runtime.
2. Đọc `~/.codex/config.toml` làm base.
3. Đọc overlay tương ứng.
4. Chỉ lấy các scalar nằm trong allowlist.
5. Lấy model catalog bằng `codex debug models`.
6. đặt `multi_agent_version = null` cho mọi model.
7. Ghi catalog mới bằng thao tác atomic.
8. Ghép scalar và `developer_instructions` vào config gốc.
9. Với Review, xóa các bảng MCP server kế thừa.
10. Tắt native agents và hai feature flag multi-agent.
11. Ghi `config.toml` bằng thao tác atomic.
12. Tạo symlink tới auth, skill, plugin và workflow dùng chung.
13. Nếu là Supervisor và chưa có notebook, khởi tạo notebook riêng.

“Atomic” ở đây nghĩa là ghi vào file tạm rồi thay thế file đích trong một bước. Nếu tiến trình hỏng giữa lúc ghi, khả năng để lại một config bị viết dở sẽ thấp hơn.

`safe_link` cũng có chốt an toàn: nếu đường dẫn đích trong runtime là file thật thay vì symlink, script dừng lại thay vì tự ý xóa file đó.

### 6.3 Vì sao chỉ override scalar allowlist?

Giả sử overlay được phép ghi đè mọi bảng trong config gốc. Một thay đổi role có thể vô tình xóa cấu hình cá nhân, trusted project hoặc feature không liên quan.

Allowlist tạo giới hạn:

```text
Overlay chỉ được thay các khóa đã duyệt
  -> config cá nhân còn lại được kế thừa
  -> thêm một quyền override mới phải sửa code và test có chủ đích
```

Nếu muốn thêm một top-level key riêng cho role, phải thêm key đó vào `OVERRIDE_KEYS` trong `codex-room-sync` và thêm test chứng minh hành vi.

## 7. Một lần chạy hoàn chỉnh diễn ra thế nào?

Giả sử người dùng chọn `Codex Peer` trong Paseo.

### Bước 1: Paseo đọc provider

Paseo thấy command đã render:

```text
/Users/alice/.local/bin/codex-room peer
```

### Bước 2: launcher yêu cầu sync

`codex-room` gọi:

```text
codex-room-sync peer
```

### Bước 3: sync ghép cấu hình

```text
~/.codex/config.toml
  + ~/.config/codex-room/overlays/peer.config.toml
  + model catalog từ codex debug models
  + các cờ tắt native agents
  = ~/.codex-runtime/peer/config.toml và catalog runtime
```

### Bước 4: sync nối tài nguyên chung

Ví dụ:

```text
~/.codex-runtime/peer/auth.json -> ~/.codex/auth.json
~/.codex-runtime/peer/skills    -> ~/.codex/skills
```

### Bước 5: Codex được khởi động

Launcher đặt:

```text
CODEX_HOME=~/.codex-runtime/peer
```

rồi thay chính tiến trình launcher bằng Codex. Từ góc nhìn Codex, thư mục Peer là HOME cấu hình của nó.

### Bước 6: session được cô lập

Codex ghi session/state mới dưới runtime Peer. Lead và Review không nhìn thấy session đó như session của chính mình, dù chúng dùng cùng auth và skill.

## 8. Cách tùy biến theo nhu cầu

### Trường hợp A: đổi model của Peer

Bạn cần đổi đồng bộ hai bề mặt:

1. `home/.config/codex-room/overlays/peer.config.toml` — runtime mặc định.
2. `home/.paseo/config.json.template` — model hiển thị/mặc định trong Paseo.

Nếu chỉ sửa overlay, runtime đổi nhưng picker Paseo có thể vẫn cũ. Nếu chỉ sửa Paseo, UI đổi nhưng Codex process có thể dùng default cũ.

### Trường hợp B: đổi cách Lead chia việc

Sửa `developer_instructions` trong overlay Lead. Không cần sửa `codex-room-sync` vì đây đã là vùng overlay được hỗ trợ.

Session Lead đang chạy có thể vẫn giữ context cũ. Chỉ dẫn mới áp dụng khi cấu hình runtime được cập nhật và một tiến trình phù hợp được khởi chạy lại.

### Trường hợp C: giảm quyền từ `danger-full-access`

Hiện cả bốn overlay và provider params đều yêu cầu `danger-full-access` với `approval_policy = "never"`. Đây là cấu hình quyền lực cao.

Muốn giảm quyền, phải xem cả:

- overlay role;
- `params` của provider Paseo;
- công cụ role thực sự cần;
- các invariant bảo mật và hành vi đang được áp dụng.

Ví dụ, đặt Review thành sandbox read-only nghe hợp lý, nhưng overlay hiện giải thích OCR preview cần ghi metadata session cục bộ. Vì vậy cần kiểm tra đường ghi thật trước khi đổi, nếu không Review có thể fail dù về mặt tổ chức nó là “behavioral read-only”.

### Trường hợp D: thêm một role mới

Đây không phải chỉ thêm một file TOML. Tối thiểu phải cập nhật:

1. `ROLE_FILES` trong `codex-room-sync`;
2. overlay mới;
3. provider mới trong Paseo template;
4. quy tắc nhận diện role hợp lệ;
5. ranh giới MCP và quyền công cụ;
6. danh sách thành phần cần phân phối;
7. các invariant về model và runtime;
8. tài liệu ownership của role.

Nếu role cần MCP, còn phải sửa allowlist injection có chủ đích. Nếu role chỉ là một trách nhiệm tạm thời của Peer, thường không nên tạo role mới vì sẽ làm topology và protocol phức tạp hơn.

### Trường hợp E: dùng ở lab hoặc test tạm

`codex-room-sync` hỗ trợ các biến môi trường như:

```text
CODEX_ROOM_LAB_ROOT
CODEX_ROOM_RUNTIME_ROOT
CODEX_ROOM_CANONICAL_HOME
CODEX_ROOM_CONFIG_HOME
CODEX_ROOM_MODEL_CATALOG
CODEX_BIN
```

Các biến này cho phép sinh runtime trong một vùng tạm, dùng config và model catalog riêng, không đụng vào HOME thật. Đây là cách phù hợp để thử overlay hoặc logic merge trong môi trường cô lập.

## 9. Những lỗi người mới hay gặp

### “Tôi sửa runtime config, sau đó thay đổi biến mất”

Runtime là output được sinh. Hãy sửa base `~/.codex/config.toml` nếu thay đổi áp dụng cho mọi role, hoặc sửa overlay nếu chỉ áp dụng cho một role.

### “Paseo không thấy bốn provider”

Kiểm tra theo thứ tự:

1. `~/.paseo/config.json` có JSON hợp lệ không;
2. command có trỏ đúng `~/.local/bin/codex-room` không;
3. `~/.local/bin` có trong PATH của daemon không;
4. daemon đã restart sau khi config đổi chưa;
5. provider có xuất hiện trong inventory của daemon không.

### “Review được gọi là read-only nhưng config là full access”

“Read-only” ở đây trước hết là hợp đồng hành vi trong developer instructions. Sandbox vẫn full access để OCR preview có thể ghi metadata vận hành. Vì enforcement kỹ thuật và enforcement bằng instruction khác nhau, đây là một ranh giới cần cân nhắc kỹ nếu dùng ngoài môi trường tin cậy.

### “Có nên đưa runtime snapshot hoặc session vào vùng chia sẻ không?”

Snapshot tóm tắt chỉ nên được đưa vào vùng chia sẻ có chủ đích sau khi xem lại. Raw session không nên chia sẻ vì có thể chứa prompt, output, đường dẫn, lệnh tool và secret.

## 10. Kết luận: nên nhớ điều gì sau khi đọc?

Nếu chỉ giữ lại sáu ý, hãy giữ sáu ý này:

1. Paseo chọn và điều phối role; Codex thực thi bên trong role.
2. `codex-room-sync` là trung tâm: nó ghép base + overlay và tạo runtime.
3. `~/.codex` là của người vận hành; bộ room không sở hữu auth hay state cá nhân.
4. Bốn role dùng chung tài nguyên ổn định nhưng tách config/session/state.
5. File mẫu là nguồn thay đổi lâu dài; runtime chỉ là kết quả được sinh ra.
6. Model, quyền và MCP thường có hơn một bề mặt cấu hình; phải giữ chúng đồng bộ.

Từ nền tảng đó, bạn có thể thay model, viết lại trách nhiệm role, giảm quyền, thay workflow hoặc thêm provider mà vẫn biết thay đổi sẽ đi qua hệ thống theo đường nào và ảnh hưởng tới đâu.
