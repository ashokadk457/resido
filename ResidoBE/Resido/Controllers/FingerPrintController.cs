using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.FingerPrintRq;
using Resido.Model.TTLockDTO.ResponseDTO.FingerPrintRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
    public class FingerPrintController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        SmsDkService _smsDkService;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public FingerPrintController(
                     ResidoDbContext context,
                     CommonDBLogic commonDBLogic,
                     TTLockService tTLockHelper,
                     IWebHostEnvironment env,
                     SmsDkService smsDkService,
                     IServiceScopeFactory serviceScopeFactory
        ) : base(context)
        {
            _context = context;
            _commonDBLogic = commonDBLogic;
            _ttLockHelper = tTLockHelper;
            _smsDkService = smsDkService;
            _serviceScopeFactory = serviceScopeFactory;
        }

        // POST: /api/Fingerprints/AddFingerprint
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<AddFingerprintResponseDTO>>> AddFingerprint([FromBody] AddFingerprintRequestDTO dto)
        {
            var response = new ResponseDTO<AddFingerprintResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();

                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == dto.LockId && a.UserId == token.UserId);

                if (smartLock == null)
                    return Ok(response.SetMessage(Resource.InvalidSmartLock));

                var result = await _ttLockHelper.AddFingerprintAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    Fingerprint fingerprint = new Fingerprint();

                    fingerprint.FingerName = dto.FingerprintName;
                    fingerprint.FingerprintId = result.Data.FingerprintId;
                    fingerprint.SmartLockId = smartLock.Id;
                    _context.Fingerprints.Add(fingerprint);
                    _context.SaveChanges();

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

        // GET: /api/Fingerprints/ListFingerprints
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<ListFingerprintResponseDTO>>> ListFingerprints([FromQuery] ListFingerprintRequestDTO dto)
        {
            var response = new ResponseDTO<ListFingerprintResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListFingerprintsAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    if (response?.Data?.List?.Any() ?? false)
                    {
                        foreach (var eKeyRecordDTO in response.Data.List)
                        {
                            var range = CommonLogic.CheckExpiry(eKeyRecordDTO.EndDate, 1);
                            eKeyRecordDTO.IsExpired = range.IsExpired;
                            eKeyRecordDTO.IsExpiringSoon = range.IsExpiringSoon;
                        }
                    }
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

        // POST: /api/Fingerprints/DeleteFingerprint
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<DeleteFingerprintResponseDTO>>> DeleteFingerprint([FromBody] DeleteFingerprintRequestDTO dto)
        {
            var response = new ResponseDTO<DeleteFingerprintResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == dto.LockId && a.UserId == token.UserId);

                if (smartLock == null)
                    return Ok(response.SetMessage(Resource.InvalidSmartLock));

                var result = await _ttLockHelper.DeleteFingerprintAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    var fingerprint = await _context.Fingerprints.FirstOrDefaultAsync(a => a.FingerprintId == dto.FingerprintId);
                    if (fingerprint != null)
                    {
                        _context.Fingerprints.Remove(fingerprint);
                        _context.SaveChanges();
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

        // POST: /api/Fingerprints/ChangeFingerprintPeriod
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<ChangeFingerprintPeriodResponseDTO>>> ChangeFingerprintPeriod([FromBody] ChangeFingerprintPeriodRequestDTO dto)
        {
            var response = new ResponseDTO<ChangeFingerprintPeriodResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ChangeFingerprintPeriodAsync(token.AccessToken, dto);

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
        // POST: /api/Fingerprints/ClearFingerprint
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<ClearFingerprintResponseDTO>>> ClearFingerprint([FromBody] ClearFingerprintRequestDTO dto)
        {
            var response = new ResponseDTO<ClearFingerprintResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ClearFingerprintAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    var fingerprints = await _context.Fingerprints.Where(a => a.SmartLock.TTLockId == dto.LockId).ToListAsync();
                    if (fingerprints != null)
                    {
                        _context.Fingerprints.RemoveRange(fingerprints);
                        _context.SaveChanges();
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

        // POST: /api/Fingerprints/RenameFingerprint
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<RenameFingerprintResponseDTO>>> RenameFingerprint([FromBody] RenameFingerprintRequestDTO dto)
        {
            var response = new ResponseDTO<RenameFingerprintResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.RenameFingerprintAsync(token.AccessToken, dto);

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
