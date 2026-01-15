using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper;
using Resido.Helper.EmailHelper;
using Resido.Helper.TokenAuthorize;
using Resido.Model;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO;
using Resido.Model.TTLockDTO.RequestDTO;
using Resido.Model.TTLockDTO.RequestDTO.EkeysRq;
using Resido.Model.TTLockDTO.RequestDTO.LockRq;
using Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;
using System.Globalization;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    [TokenAuthorize]
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
        // POST: /api/Ekeys/GetAllEkeys
        [HttpPost]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<ListKeysResponseDTO>>> GetAllEkeys([FromBody] EkeysRequestDTO dto)
        {
            var response = new ResponseDTO<ListKeysResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                // 🔑 Step 1: Get lock list of the account
                var lockListRequest = new ListLocksRequestDTO
                {
                    PageNo = 1,
                    PageSize = 1000, // fetch all locks
                    GroupId = dto.GroupId,
                    LockAlias = dto.LockAlias
                };

                var lockListResponse = await _ttLockHelper.ListLocksAsync(lockListRequest, token.AccessToken);


                // 🔑 Step 3: Get eKeys for the lock
                var listRequest = new ListKeysRequestDTO
                {
                    AccessToken = token.AccessToken,
                    PageNo = dto.PageNo,
                    PageSize = dto.PageSize,
                    LockAlias = dto.LockAlias,
                    GroupId = dto.GroupId
                };

                var ekeyResponse = await _ttLockHelper.ListKeysAsync(listRequest);
                if (ekeyResponse.IsSuccessCode())
                {
                    
                    if (ekeyResponse?.Data?.List?.Any() ?? false)
                    {

                        // If lock list is NULL → set HasGateway = false for all
                        if (lockListResponse?.Data?.List == null)
                        {
                            ekeyResponse.Data.List.ForEach(k =>
                            {
                                if (k != null)
                                    k.HasGateway = 0;
                            });

                        }
                        else
                        {
                            // Create lookup dictionary
                            var lockGatewayMap = lockListResponse.Data.List
                                .Where(x => x != null)
                                .ToDictionary(x => x.LockId, x => x.HasGateway);

                            // Map values
                            foreach (var key in ekeyResponse.Data.List)
                            {
                                if (key == null)
                                    continue;

                                key.HasGateway = lockGatewayMap.TryGetValue(key.LockId, out var hasGateway)
                                    ? hasGateway
                                    : 0;
                            }

                        }
                        response.Data = ekeyResponse.Data;
                    }
                    response.SetSuccess();
                }
                else
                {
                    response.SetMessage(ekeyResponse.Message);
                }
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }
        // GET: /api/Locks/ListEKeys
        [HttpGet]
        public async Task<ActionResult<ResponseDTO<ListEKeysResponseDTO>>> ListEKeys([FromQuery] ListEKeysRequestDTO dto)
        {
            var response = new ResponseDTO<ListEKeysResponseDTO>();
            response.SetFailed();

            try
            {
                var token = await GetAccessTokenEntityAsync();
                if (!token.IsValidAccessToken())
                    return Ok(response.SetMessage(Resource.InvalidAccessToken));

                var result = await _ttLockHelper.ListEKeysAsync(token.AccessToken, dto);

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

                // Normalize receiver input (email or phone) to ensure consistent lookup and validation
                var contactOrEmail = dto.ReceiverUsername.NormalizeInput();

                // Validate whether the receiver exists in the system using email/phone and dial code
                var (userTo, _, error) = await _commonDBLogic.GetAndValidateUserAsync(contactOrEmail, dto.DialCode);
                if (error != null)
                    return Ok(response.SetMessage(error));

                // =========================
                // Existing User Flow
                // =========================
                if (userTo != null)
                {
                    // Use system-generated TTLock username for sending eKey
                    dto.ReceiverUsername = userTo.TTLockUsername;

                    var sendResponse = await _ttLockHelper.SendKeyAsync(token.AccessToken, dto);

                    if (sendResponse.IsSuccessCode())
                    {
                        response.Data = sendResponse.Data;

                        // Send welcome email and SMS asynchronously without blocking the API response
                        _ = Task.Run(async () =>
                        {
                            using var scope = _serviceScopeFactory.CreateScope();

                            try
                            {
                                var scopedSmsService = scope.ServiceProvider.GetRequiredService<SmsDkService>();

                                // Send welcome email (existing user)
                                if (!string.IsNullOrEmpty(userTo.Email))
                                    await SendWelcomeEmailAsync(userTo.Email, string.Empty, true);

                                // Send notification SMS
                                if (!string.IsNullOrEmpty(userTo.PhoneNumber))
                                {
                                    string contact = $"{userTo.DialCode}{userTo.PhoneNumber}";
                                    string body = await SmsContentHelper.GetSmsContentForExistingUserAsync(
                                        CultureInfo.CurrentCulture.Name, contact
                                    );

                                    await scopedSmsService.SendSmsAsync(new SmsDkService.SmsRequestDto
                                    {
                                        Receiver = contact,
                                        Message = body
                                    });
                                }
                            }
                            catch
                            {
                                // Intentionally ignored to avoid notification failure impacting API response
                            }
                        });

                        return Ok(response.SetSuccess());
                    }

                    return Ok(response.SetMessage(sendResponse?.Data?.Errmsg));
                }

                // =========================
                // New User Creation Flow
                // =========================

                // Create a new internal ZAFE user using the provided email/phone
                userTo ??= CreateNewUser(contactOrEmail, dto.DialCode, response);
                if (userTo == null)
                    return Ok(response); // Validation for new user failed

                // Register the new user in TTLock and generate credentials
                var (success, password, user) = await RegisterTTLockUserAsync(userTo, contactOrEmail);
                if (!success)
                    return Ok(response.SetMessage(Resource.ZafeAccountCreationError));

                // Persist user with TTLock credentials
                userTo.IsEkeysSingnUp = true;
                userTo.TTLockHashPassword = user.TTLockHashPassword;
                userTo.TTLockUsername = user.TTLockUsername;
                await AddUserToDb(userTo);

                // Use TTLock username to send eKey
                dto.ReceiverUsername = userTo.TTLockUsername;

                var retryResponse = await _ttLockHelper.SendKeyAsync(token.AccessToken, dto);
                if (retryResponse.IsSuccessCode())
                {
                    // Send welcome email and SMS (new user) asynchronously
                    _ = Task.Run(async () =>
                    {
                        using var scope = _serviceScopeFactory.CreateScope();

                        try
                        {
                            var scopedSmsService = scope.ServiceProvider.GetRequiredService<SmsDkService>();

                            // Send welcome email including generated password
                            if (!string.IsNullOrEmpty(userTo.Email))
                                await SendWelcomeEmailAsync(userTo.Email, password, false);

                            // Send SMS containing TTLock credentials
                            if (!string.IsNullOrEmpty(userTo.PhoneNumber))
                            {
                                string contact = $"{userTo.DialCode}{userTo.PhoneNumber}";
                                string body = await SmsContentHelper.GetSmsContentAsync(
                                    CultureInfo.CurrentCulture.Name, contact, password
                                );

                                await scopedSmsService.SendSmsAsync(new SmsDkService.SmsRequestDto
                                {
                                    Receiver = contact,
                                    Message = body
                                });
                            }
                        }
                        catch
                        {
                            // Intentionally ignored to prevent notification issues from affecting API response
                        }
                    });

                    return Ok(response.SetSuccess());
                }

                return Ok(response.SetMessage(retryResponse.Message));
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        private async Task<(bool success, string password, User user)> RegisterTTLockUserAsync(User user, string contactOrEmail)
        {
            string password = PasswordHelper.GenerateRandomPassword();
            string ttlockPassword = PasswordHelper.GenerateMd5ForTTLock(password);

            // Generate temporary username for TTLock
            user.TTLockUsername = CommonLogic.GenerateUserName(user);

            // Call TTLock API
            var registerResponse = await _ttLockHelper.RegisterUserAsync(user.TTLockUsername, ttlockPassword);

            // If registration failed
            if (registerResponse?.Data?.Username == null)
                return (false, password, user);

            // Update user values
            user.TTLockUsername = registerResponse.Data.Username;

            // Set default fields
            CommonLogic.SetDefaultUserInfo(user);

            // Return user object
            return (true, password, user);
        }
        private User? CreateNewUser(string contactOrEmail, string dialCode, ResponseDTO<SendKeyResponseDTO> response)
        {
            var user = new User();

            if (UserInputValidator.ValidateEmail(contactOrEmail, out string emailError))
            {
                user.Email = contactOrEmail;
                user.IsEmailVerified = true;
            }
            else
            {
                if (!UserInputValidator.ValidatePhoneNumber(contactOrEmail, out string phoneError))
                {
                    response.SetMessage(phoneError);
                    return null;
                }
                if (!UserInputValidator.ValidateDialCode(dialCode, out string dialCodeError))
                {
                    response.SetMessage(dialCodeError);
                    return null;
                }
                user.PhoneNumber = contactOrEmail;
                user.DialCode = dialCode;
                user.IsPhoneVerified = true;
                user.IsEkeysSingnUp = true;
            }

            return user;
        }

        private async Task AddUserToDb(User user)
        {
            //user.TTLockUsername ??= CommonLogic.GenerateUserName(contactOrEmail);
            CommonLogic.SetDefaultUserInfo(user);
            _context.Users.Add(user);
            await _context.SaveChangesAsync();
        }

        private async Task SendWelcomeEmailAsync(string? email, string password, bool isExistingUser)
        {
            if (!UserInputValidator.ValidateEmail(email, out string emailError)) return;

            if (isExistingUser)
            {

                var (subject, html) = EmailTemplates.BuildExistingUserEmailHtml(
                email.Split('@')[0], email, CultureInfo.CurrentCulture.Name);

                var mailRequest = new MailRequestModel
                {
                    ToEmail = email,
                    Body = html,
                    Subject = Resource.WelcomeToZafeLockEkeySubject
                };
                await MailHelper.SendEmailAsync(mailRequest);
            }
            else
            {
                var (subject, html) = EmailTemplates.BuildWelcomeEmailHtml(
                email.Split('@')[0], email, password, CultureInfo.CurrentCulture.Name);

                var mailRequest = new MailRequestModel
                {
                    ToEmail = email,
                    Body = html,
                    Subject = Resource.WelcomeToZafeLockEkeySubject
                };
                await MailHelper.SendEmailAsync(mailRequest);
            }




        }


        // POST: /api/Ekeys/DeleteEkey
        [HttpDelete]
        [TokenAuthorize]
        public async Task<ActionResult<ResponseDTO<DeleteKeyResponseDTO>>> DeleteEkey(int keyId)
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
