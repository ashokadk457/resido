using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Resido.Database;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.LockRq;
using Resido.Model.TTLockDTO.ResponseDTO.LockRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
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

        // POST: /api/Lock/SetAutoLockTime
        [HttpPost]
        [TokenAuthorize]
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



    }
}
