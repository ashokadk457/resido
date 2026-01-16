using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Resido.Database;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.LockRq;
using Resido.Model.TTLockDTO.RequestDTO.LockSettingRq;
using Resido.Model.TTLockDTO.ResponseDTO.LockSettingRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
    public class LockSettingController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public LockSettingController(
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
        // POST: /api/Locks/ModifyLockSettings
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<ModifyLockSettingsResponseDTO>>> ModifyLockSettings([FromBody] ModifyLockSettingsRequestDTO dto)
        {
            var response = new ResponseDTO<ModifyLockSettingsResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ModifyLockSettingsAsync(token.AccessToken, dto);

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

        // POST: /api/Locks/SetAutoLockTime
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<SetAutoLockTimeResponseDTO>>> SetAutoLockTime([FromBody] SetAutoLockTimeRequestDTO dto)
        {
            var response = new ResponseDTO<SetAutoLockTimeResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.SetAutoLockTimeAsync(token.AccessToken, dto);

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


        // POST: /api/Locks/UpdateLockData
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<UpdateLockDataResponseDTO>>> UpdateLockData([FromBody] UpdateLockDataRequestDTO dto)
        {
            var response = new ResponseDTO<UpdateLockDataResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.UpdateLockDataAsync(token.AccessToken, dto);

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


        // POST: /api/Locks/LockUpgradeCheck
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<LockUpgradeCheckResponseDTO>>> LockUpgradeCheck([FromBody] LockUpgradeCheckRequestDTO dto)
        {
            var response = new ResponseDTO<LockUpgradeCheckResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.LockUpgradeCheckAsync(token.AccessToken, dto);

                if (result != null && result.IsSuccessCode())
                {
                    response.Data = result.Data;
                   
                    // Optional: interpret upgrade status
                    if (result.Data.NeedUpgrade == 0)
                        response.SetMessage("Lock firmware is up to date.");
                    else if (result.Data.NeedUpgrade == 1)
                        response.SetMessage($"Upgrade available: {result.Data.Version}");
                    else
                        response.SetMessage("Upgrade status unknown. Please recheck with lockData via APP SDK.");

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

        // POST: /api/Locks/LockUpgradeRecheck
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<LockUpgradeRecheckResponseDTO>>> LockUpgradeRecheck([FromBody] LockUpgradeRecheckRequestDTO dto)
        {
            var response = new ResponseDTO<LockUpgradeRecheckResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.LockUpgradeRecheckAsync(token.AccessToken, dto);

                if (result != null && result.IsSuccessCode())
                {
                    response.Data = result.Data;
                    response.SetSuccess();

                    // Optional: interpret upgrade status
                    if (result.Data.NeedUpgrade == 0)
                        response.SetMessage("Lock firmware is up to date.");
                    else if (result.Data.NeedUpgrade == 1)
                        response.SetMessage($"Upgrade available: {result.Data.Version}");
                    else
                        response.SetMessage("Upgrade status unknown. Please recheck again with latest lockData.");
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
