using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.Database;
using Resido.Helper;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.LockRq;
using Resido.Model.TTLockDTO.ResponseDTO.LockRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
    public class LockController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public LockController(
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
        // GET: /api/Locks/ListLocks
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<ListLocksResponseDTO>>> ListLocks([FromQuery] ListLocksRequestDTO dto)
        {
            var response = new ResponseDTO<ListLocksResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListLocksAsync(dto, token.AccessToken);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    //no need for now
                    //if (response.Data?.List?.Any() == true)
                    //{
                    //    var ttLockIds = response.Data.List.Select(x => x.LockId).ToList();

                    //    var smartLocks = await _context.SmartLocks
                    //        .Where(x => ttLockIds.Contains(x.TTLockId) && x.UserId == token.UserId)
                    //        .ToListAsync();

                    //    var smartLockIds = smartLocks.Select(x => x.Id).ToList();

                    //    var usageCounts = await GetSmartLockUsageCountsAsync(smartLockIds);

                    //    foreach (var lockDto in response.Data.List)
                    //    {
                    //        var smartLock = smartLocks.FirstOrDefault(x => x.TTLockId == lockDto.LockId);
                    //        if (smartLock == null) continue;

                    //        if (usageCounts.TryGetValue(smartLock.Id, out var usage))
                    //        {
                    //            lockDto.PinCodeCount = usage.PinCodeCount;
                    //            lockDto.PinCodeLimitCount = usage.PinCodeLimitCount;

                    //            lockDto.CardCount = usage.CardCount;
                    //            lockDto.CardLimitCount = usage.CardLimitCount;

                    //            lockDto.FingerprintCount = usage.FingerprintCount;
                    //            lockDto.FingerprintLimitCount = usage.FingerprintLimitCount;

                    //            lockDto.EkeyCount = usage.EkeyCount;
                    //            lockDto.EkeyLimitCount = usage.EkeyLimitCount;
                    //        }
                    //    }
                    //}
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result.Message);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // GET: /api/Locks/GetLockDetail
        [HttpGet]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<GetLockDetailResponseDTO>>> GetLockDetail(int lockId)
        {
            var response = new ResponseDTO<GetLockDetailResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.GetLockDetailAsync(token.AccessToken, lockId);

                if (result != null && result.Data != null && result.IsSuccessCode())
                {
                    response.Data = new GetLockDetailResponseDTO();

                    response.Data = result.Data;
                    var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(x => x.TTLockId == lockId && x.UserId == token.UserId);
                    if (smartLock != null)
                    {
                        var usageCounts = await _commonDBLogic.GetSmartLockUsageCountsAsync(
                            new List<Guid> { smartLock.Id });

                        var usage = usageCounts[smartLock.Id];

                        response.Data.PinCodeCount = usage.PinCodeCount;
                        response.Data.PinCodeLimitCount = usage.PinCodeLimitCount;

                        response.Data.CardCount = usage.CardCount;
                        response.Data.CardLimitCount = usage.CardLimitCount;

                        response.Data.FingerprintCount = usage.FingerprintCount;
                        response.Data.FingerprintLimitCount = usage.FingerprintLimitCount;

                        response.Data.EkeyCount = usage.EkeyCount;
                        response.Data.EkeyLimitCount = usage.EkeyLimitCount;
                    }
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }



        // POST: /api/Lock/InitializeLock
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<InitializeLockResponseDTO>>> InitializeLock([FromBody] InitializeLockRequestDTO dto)
        {
            var response = new ResponseDTO<InitializeLockResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.InitializeLockAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    var lockId = result.Data.LockId;

                    var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == lockId);

                    if (smartLock != null)
                    {
                        smartLock = new Database.DBTable.SmartLock();
                        smartLock.Mac = dto.Mac;
                        smartLock.AliasName = dto.LockAlias;
                        smartLock.Name = dto.LockAlias;
                        smartLock.LockData = dto.LockData;
                        smartLock.Category = dto.Category;
                        smartLock.Location = dto.Location;
                        smartLock.TTLockId = lockId;
                        smartLock.UserId = token.UserId;
                        smartLock.UpdatedAt = DateTimeHelper.GetUtcTime();
                    }
                    else
                    {
                        smartLock = new Database.DBTable.SmartLock();
                        smartLock.Mac = dto.Mac;
                        smartLock.AliasName = dto.LockAlias;
                        smartLock.Name = dto.LockAlias;
                        smartLock.LockData = dto.LockData;
                        smartLock.TTLockId = lockId;
                        smartLock.UserId = token.UserId;
                        smartLock.Category = dto.Category;
                        smartLock.Location = dto.Location;
                        smartLock.CreatedAt = DateTimeHelper.GetUtcTime();
                        smartLock.UpdatedAt = DateTimeHelper.GetUtcTime();
                        _context.SmartLocks.Add(smartLock);
                    }
                    await _context.SaveChangesAsync();
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/Lock/DeleteLock
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<DeleteLockResponseDTO>>> DeleteLock([FromBody] DeleteLockRequestDTO dto)
        {
            var response = new ResponseDTO<DeleteLockResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.DeleteLockAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    var smartLock = await _context.SmartLocks
                        .Include(a => a.Cards)
                        .Include(a => a.PinCodes)
                        .Include(a => a.Fingerprints)
                        .Include(a => a.EKeys)
                        .Include(a => a.AccessLogs)
                        .FirstOrDefaultAsync(a => a.TTLockId == dto.LockId);
                    if (smartLock != null)
                    {
                        _context.SmartLocks.Remove(smartLock);
                        await _context.SaveChangesAsync();
                    }
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/Lock/RenameLock
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<RenameLockResponseDTO>>> RenameLock([FromBody] RenameLockRequestDTO dto)
        {
            var response = new ResponseDTO<RenameLockResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.RenameLockAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

    }
}
