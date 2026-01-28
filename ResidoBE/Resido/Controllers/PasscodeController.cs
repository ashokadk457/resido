using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper.TokenAuthorize;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO.PasscodeRq;
using Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
    public class PasscodeController : BaseApiController
    {
        ResidoDbContext _context;
        CommonDBLogic _commonDBLogic;
        TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public PasscodeController(
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
        // POST: /api/Passcodes/GetKeyboardPwd
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<GetKeyboardPwdResponseDTO>>> GetKeyboardPwd([FromBody] GetKeyboardPwdRequestDTO dto)
        {
            var response = new ResponseDTO<GetKeyboardPwdResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == dto.LockId && a.UserId == token.UserId);

                if (smartLock == null)
                    return Ok(response.SetMessage(Resource.InvalidSmartLock));

                var result = await _ttLockHelper.GetKeyboardPwdAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    PinCode pin = new PinCode();

                    pin.KeyboardPwdId = result.Data.KeyboardPwdId;
                    pin.SmartLockId = smartLock.Id;
                    _context.PinCodes.Add(pin);
                    _context.SaveChanges();

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
        // POST: /api/Passcodes/AddKeyboardPwd
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<AddKeyboardPwdResponseDTO>>> AddKeyboardPwd([FromBody] AddKeyboardPwdRequestDTO dto)
        {
            var response = new ResponseDTO<AddKeyboardPwdResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();

                var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == dto.LockId && a.UserId == token.UserId);

                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                if (smartLock == null)
                    return Ok(response.SetMessage(Resource.InvalidSmartLock));

                var result = await _ttLockHelper.AddKeyboardPwdAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    PinCode pin = new PinCode();

                    pin.Pin = dto.KeyboardPwd;
                    pin.KeyboardPwdId = result.Data.KeyboardPwdId;
                    pin.SmartLockId = smartLock.Id;
                    _context.PinCodes.Add(pin);
                    _context.SaveChanges();
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

        // GET: /api/Passcodes/ListKeyboardPwd
        [HttpGet]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ListKeyboardPwdResponseDTO>>> ListKeyboardPwd([FromQuery] ListKeyboardPwdRequestDTO dto)
        {
            var response = new ResponseDTO<ListKeyboardPwdResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListKeyboardPwdAsync(token.AccessToken, dto);

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

        // POST: /api/Passcodes/DeleteKeyboardPwd
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<DeleteKeyboardPwdResponseDTO>>> DeleteKeyboardPwd([FromBody] DeleteKeyboardPwdRequestDTO dto)
        {
            var response = new ResponseDTO<DeleteKeyboardPwdResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));


                var result = await _ttLockHelper.DeleteKeyboardPwdAsync(token.AccessToken, dto);

                if (result.IsSuccessCode())
                {
                    var pinCode = await _context.PinCodes.FirstOrDefaultAsync(a => a.KeyboardPwdId == dto.KeyboardPwdId);
                    if (pinCode != null)
                    {
                        _context.PinCodes.Remove(pinCode);
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

        // POST: /api/Passcodes/ChangeKeyboardPwd
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ChangeKeyboardPwdResponseDTO>>> ChangeKeyboardPwd([FromBody] ChangeKeyboardPwdRequestDTO dto)
        {
            var response = new ResponseDTO<ChangeKeyboardPwdResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ChangeKeyboardPwdAsync(token.AccessToken, dto);

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
