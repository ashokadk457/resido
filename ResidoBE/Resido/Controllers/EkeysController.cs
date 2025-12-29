using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Resido.Database;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO;
using Resido.Model.TTLockDTO.RequestDTO;
using Resido.Model.TTLockDTO.RequestDTO.EkeysRq;
using Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    public class EkeysController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        SmsDkService _smsDkService;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public EkeysController(
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
        // POST: /api/Ekeys/GetAllEkeys
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ListKeysResponseDTO>>> GetAllEkeys([FromBody] EkeysRequestDTO dto)
        {
            var response = new ResponseDTO<ListKeysResponseDTO>();
            response.SetSuccess();

            try
            {
                var token = await GetAccessTokenEntityAsync();

                // 🔑 Build request DTO for TTLock
                var listRequest = new ListKeysRequestDTO
                {
                    AccessToken = token.AccessToken,
                    PageNo = dto.PageNo,
                    PageSize = dto.PageSize,
                    LockAlias = dto.LockAlias,   // optional, if you extend EkeysRequestDTO
                    GroupId = dto.GroupId        // optional, if you extend EkeysRequestDTO
                };

                // 🔑 Call TTLock service with dynamic pageNo and pageSize
                var ekeyResponse = await _ttLockHelper.ListKeysAsync(listRequest);

                if (ekeyResponse?.Data?.List?.Any() ?? false)
                {
                    response.Data = ekeyResponse.Data;
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }


        // POST: /api/Ekeys/SendKey
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<SendKeyResponseDTO>>> SendKey([FromBody] SendKeyRequestDTO dto)
        {
            var response = new ResponseDTO<SendKeyResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
              
                var sendResponse = await _ttLockHelper.SendKeyAsync(token.AccessToken, dto);

                if (sendResponse.IsSuccessCode())
                {
                    response.Data = sendResponse.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(sendResponse?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }


        // POST: /api/Ekeys/DeleteEkey
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<DeleteKeyResponseDTO>>> DeleteEkey([FromBody] int keyId)
        {
            var response = new ResponseDTO<DeleteKeyResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();

                var deleteResponse = await _ttLockHelper.DeleteKeyAsync(token.AccessToken, keyId);

                if (deleteResponse?.Data != null && deleteResponse.Data.Errcode == 0)
                {
                    response.Data = deleteResponse.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(deleteResponse?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }
        // POST: /api/Ekeys/UnfreezeEkey
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<UnfreezeKeyResponseDTO>>> UnfreezeEkey([FromBody] int keyId)
        {
            var response = new ResponseDTO<UnfreezeKeyResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();

                var unfreezeResponse = await _ttLockHelper.UnfreezeKeyAsync(token.AccessToken, keyId);

                if (unfreezeResponse?.Data != null && unfreezeResponse.Data.Errcode == 0)
                {
                    response.Data = unfreezeResponse.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(unfreezeResponse?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }


        // POST: /api/Ekeys/UpdateEkey
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<UpdateKeyResponseDTO>>> UpdateEkey([FromBody] UpdateKeyRequestDTO dto)
        {
            var response = new ResponseDTO<UpdateKeyResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.UpdateKeyAsync(token.AccessToken, dto);

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

        // POST: /api/Ekeys/ChangePeriod
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ChangeKeyPeriodResponseDTO>>> ChangePeriod([FromBody] ChangeKeyPeriodRequestDTO dto)
        {
            var response = new ResponseDTO<ChangeKeyPeriodResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ChangeKeyPeriodAsync(token.AccessToken, dto);

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


        // POST: /api/Ekeys/AuthorizeKey
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<KeyAuthorizeResponseDTO>>> AuthorizeKey([FromBody] KeyAuthorizeRequestDTO dto)
        {
            var response = new ResponseDTO<KeyAuthorizeResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();

                var authorizeResponse = await _ttLockHelper.AuthorizeKeyAsync(
                    token.AccessToken,
                    dto.LockId,
                    dto.KeyId);

                if (authorizeResponse?.Data != null && authorizeResponse.Data.Errcode == 0)
                {
                    response.Data = authorizeResponse.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(authorizeResponse?.Data?.Errmsg);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        // POST: /api/Ekeys/UnauthorizeKey
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<KeyUnauthorizeResponseDTO>>> UnauthorizeKey([FromBody] KeyUnauthorizeRequestDTO dto)
        {
            var response = new ResponseDTO<KeyUnauthorizeResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
               
                var unauthorizeResponse = await _ttLockHelper.UnauthorizeKeyAsync(
                    token.AccessToken,
                    dto.LockId,
                    dto.KeyId);

                if (unauthorizeResponse?.Data != null && unauthorizeResponse.Data.Errcode == 0)
                {
                    response.Data = unauthorizeResponse.Data;
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(unauthorizeResponse?.Data?.Errmsg);
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
