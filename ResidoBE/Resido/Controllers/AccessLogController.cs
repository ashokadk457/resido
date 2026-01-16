using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.DTO;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [TokenAuthorize]
    public class AccessLogController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public AccessLogController(
                     ResidoDbContext context,
                     CommonDBLogic commonDBLogic,
                     TTLockService tTLockHelper,
                     IWebHostEnvironment env,
                     IServiceScopeFactory serviceScopeFactory
        ) : base(context)
        {
            _context = context;
            _commonDBLogic = commonDBLogic;
            _ttLockHelper = tTLockHelper;
            _serviceScopeFactory = serviceScopeFactory;
        }
   // GET: api/AccessLog/GetAccessLogs
[HttpGet]
        public async Task<ActionResult<PaginatedResponseDTO<AccessLogDayGroupDTO>>> GetAccessLogs(
    int pageNo = 1,
    int pageSize = 40,
    int lockId = 0,                               // REQUIRED
    AccessRecordType? recordType = null,          // Optional
    long? startDate = null,
    long? endDate = null,
    string? searchText = null
)
        {
            var response = new PaginatedResponseDTO<AccessLogDayGroupDTO>();

            try
            {
                // 1️⃣ Validate access token
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                // 2️⃣ Validate lockId
                if (lockId <= 0)
                    return Ok(response.SetMessage("LockId is required."));

                // 3️⃣ Validate SmartLock ownership
                var smartLock = await _context.SmartLocks
                    .AsNoTracking()
                    .FirstOrDefaultAsync(x => x.TTLockId == lockId && x.UserId == token.UserId);

                if (smartLock == null)
                    return Ok(response.SetMessage(Resource.InvalidSmartLock));

                // 4️⃣ Pagination safety
                if (pageNo <= 0) pageNo = 1;
                if (pageSize <= 0) pageSize = 40;

                // 5️⃣ Base query
                IQueryable<AccessLog> query = _context.AccessLogs
                    .Where(x => x.LockId == lockId && x.SmartLockId == smartLock.Id);

                // 6️⃣ RecordType filter (optional)
                if (recordType.HasValue)
                {
                    query = query.Where(x => x.RecordType == (int)recordType.Value);
                }

                // 7️⃣ Date filters (CreatedAt – UTC)
                if (startDate.HasValue)
                {
                    var startUtc = DateTimeOffset
                        .FromUnixTimeMilliseconds(startDate.Value)
                        .UtcDateTime;

                    query = query.Where(x => x.CreatedAt >= startUtc);
                }

                if (endDate.HasValue)
                {
                    var endUtc = DateTimeOffset
                        .FromUnixTimeMilliseconds(endDate.Value)
                        .UtcDateTime;

                    query = query.Where(x => x.CreatedAt <= endUtc);
                }

                // 8️⃣ Text search
                if (!string.IsNullOrWhiteSpace(searchText))
                {
                    searchText = searchText.Trim().ToLower();

                    query = query.Where(x =>
                        (x.Username != null && x.Username.ToLower().Contains(searchText)) ||
                        (x.LockMac != null && x.LockMac.ToLower().Contains(searchText)) ||
                        (x.RecordTypeDescription != null && x.RecordTypeDescription.ToLower().Contains(searchText)) ||
                        (x.KeyboardPwd != null && x.KeyboardPwd.ToLower().Contains(searchText))
                    );
                }

                // 9️⃣ Total count (before grouping)
                var totalRecords = await query.CountAsync();
                var totalPages = (int)Math.Ceiling(totalRecords / (double)pageSize);

                // 🔟 Fetch paginated records
                var logs = await query
                    .OrderByDescending(x => x.LockEventUtcTime)
                    .Skip((pageNo - 1) * pageSize)
                    .Take(pageSize)
                    .AsNoTracking()
                    .ToListAsync();

                // 1️⃣1️⃣ Map to flat DTO list
                var flatLogs = logs.Select(x => new AccessLogResponseDTO
                {
                    Id = x.Id,
                    LockId = x.LockId,
                    LockMac = x.LockMac,
                    RecordType = x.RecordType,
                    RecordTypeDescription = x.RecordTypeDescription,
                    Username = x.Username,
                    KeyboardPwd = x.KeyboardPwd,
                    BatteryPercentage = x.BatteryPercentage,
                    IsAccessSuccessful = x.IsAccessSuccessful,
                    LockEventUtcTime = x.LockEventUtcTime,
                    ServerReceivedUtcTime = x.ServerReceivedUtcTime,
                    CreatedAt = x.CreatedAt
                }).ToList();

                // 1️⃣2️⃣ Group by day (UTC) + time-wise ordering
                var groupedResult = flatLogs
                    .GroupBy(x => x.LockEventUtcTime.Date)
                    .OrderByDescending(g => g.Key) // Latest day first
                    .Select(g => new AccessLogDayGroupDTO
                    {
                        Date = g.Key,
                        Logs = g
                            .OrderByDescending(x => x.LockEventUtcTime) // Latest time first
                            .ToList()
                    })
                    .ToList();

                // 1️⃣3️⃣ Final response
                response.Data = groupedResult;
                response.PageNo = pageNo;
                response.PageSize = pageSize;
                response.TotalPages = totalPages;
                response.TotalRecords = totalRecords;
                response.IsSuccess = true;

                return Ok(response);
            }
            catch (Exception ex)
            {
                return Ok(response.SetMessage(ex.Message));
            }
        }
    }
}
