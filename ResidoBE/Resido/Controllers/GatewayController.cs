using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Resido.Database;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.GatewayRq;
using Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
    public class GatewayController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public GatewayController(
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
        // POST: /api/Locks/RemoteLock
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<RemoteLockResponseDTO>>> RemoteLock([FromBody] RemoteLockRequestDTO dto)
        {
            var response = new ResponseDTO<RemoteLockResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.RemoteLockAsync(token.AccessToken, dto);

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

        // POST: /api/Locks/UnlockLock
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<UnlockLockResponseDTO>>> UnlockLock([FromBody] UnlockLockRequestDTO dto)
        {
            var response = new ResponseDTO<UnlockLockResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.UnlockLockAsync(token.AccessToken, dto);

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

        // GET: /api/Locks/QueryLockDate
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<QueryLockDateResponseDTO>>> QueryLockDate([FromQuery] QueryLockDateRequestDTO dto)
        {
            var response = new ResponseDTO<QueryLockDateResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.QueryLockDateAsync(token.AccessToken, dto);

                if (result != null && result.IsSuccessCode())
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

        // POST: /api/Locks/UpdateLockDate
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<UpdateLockDateResponseDTO>>> UpdateLockDate([FromBody] UpdateLockDateRequestDTO dto)
        {
            var response = new ResponseDTO<UpdateLockDateResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                // Use current UTC timestamp if not provided
                if (dto.Date <= 0)
                    dto.Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

                var result = await _ttLockHelper.UpdateLockDateAsync(token.AccessToken, dto);

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
        // GET: /api/Gateways/ListGateways
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<ListGatewaysResponseDTO>>> ListGateways([FromQuery] ListGatewaysRequestDTO dto)
        {
            var response = new ResponseDTO<ListGatewaysResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListGatewaysAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    response.Data = result.Data;
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

        // POST: /api/Gateways/DeleteGateway
        [HttpDelete]
        public async Task<ActionResult<ResponseDTO<DeleteGatewayResponseDTO>>> DeleteGateway(int gatewayId)
        {
            var response = new ResponseDTO<DeleteGatewayResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.DeleteGatewayAsync(token.AccessToken, new DeleteGatewayRequestDTO { GatewayId= gatewayId });

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

        // POST: /api/Gateways/RenameGateway
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<RenameGatewayResponseDTO>>> RenameGateway([FromBody] RenameGatewayRequestDTO dto)
        {
            var response = new ResponseDTO<RenameGatewayResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.RenameGatewayAsync(token.AccessToken, dto);

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


        // GET: /api/Gateways/ListGatewayLocks
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<ListGatewayLocksResponseDTO>>> ListGatewayLocks(int gatewayId)
        {
            var response = new ResponseDTO<ListGatewayLocksResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListGatewayLocksAsync(token.AccessToken, gatewayId);

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

        // GET: /api/Gateways/ListGatewaysByLock
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<ListGatewaysByLockResponseDTO>>> ListGatewaysByLock(int lockId)
        {
            var response = new ResponseDTO<ListGatewaysByLockResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListGatewaysByLockAsync(token.AccessToken, lockId);

                if (result != null && result.Data?.List?.Any() == true && result.IsSuccessCode())
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
        // GET: /api/Gateways/GetGatewayDetail
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<GetGatewayDetailResponseDTO>>> GetGatewayDetail(int gatewayId)
        {
            var response = new ResponseDTO<GetGatewayDetailResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.GetGatewayDetailAsync(token.AccessToken, gatewayId);

                if (result != null && result.IsSuccessCode())
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
        // POST: /api/Gateways/IsInitSuccess
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<IsGatewayInitSuccessResponseDTO>>> IsInitSuccess([FromBody] IsGatewayInitSuccessRequestDTO dto)
        {
            var response = new ResponseDTO<IsGatewayInitSuccessResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.IsGatewayInitSuccessAsync(token.AccessToken, dto);

                if (result != null && result.IsSuccessCode() && result.Data?.GatewayId > 0)
                {
                    response.Data = result.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(result?.Data?.Errmsg ?? "Gateway initialization not confirmed.");
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }
        // POST: /api/Gateways/UploadGatewayDetail
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<UploadGatewayDetailResponseDTO>>> UploadGatewayDetail([FromBody] UploadGatewayDetailRequestDTO dto)
        {
            var response = new ResponseDTO<UploadGatewayDetailResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.UploadGatewayDetailAsync(token.AccessToken, dto);

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

        // GET: /api/Gateways/GatewayUpgradeCheck
        [HttpGet]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<GatewayUpgradeCheckResponseDTO>>> GatewayUpgradeCheck([FromQuery] GatewayRequestDTO dto)
        {
            var response = new ResponseDTO<GatewayUpgradeCheckResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.GatewayUpgradeCheckAsync(token.AccessToken, dto);

                if (result != null && result.IsSuccessCode())
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

        // POST: /api/Gateways/SetUpgradeMode
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<SetGatewayUpgradeModeResponseDTO>>> SetUpgradeMode([FromBody] GatewayRequestDTO dto)
        {
            var response = new ResponseDTO<SetGatewayUpgradeModeResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.SetGatewayUpgradeModeAsync(token.AccessToken, dto);

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
