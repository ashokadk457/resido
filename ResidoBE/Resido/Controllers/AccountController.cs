using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper;
using Resido.Model.AuthDTO;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.ResponseDTO;
using Resido.Resources;
using Resido.Services;
using Resido.Services.DAL;
using System.Globalization;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    public class AccountController : ControllerBase
    {
        private readonly ResidoDbContext _context;
        private readonly ILogger<AccountController> _logger;
        private readonly CommonDBLogic _commonDBLogic;
        private readonly TTLockService _ttLockHelper;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        private readonly OtpService _otpService;
        private readonly IConfiguration _configuration;

        public AccountController(ResidoDbContext context, ILogger<AccountController> logger, CommonDBLogic commonDBLogic,
            TTLockService tTLockHelper, IServiceScopeFactory serviceScopeFactory, OtpService otpService, IConfiguration configuration)
        {
            _context = context;
            _logger = logger;
            _commonDBLogic = commonDBLogic;
            _ttLockHelper = tTLockHelper;
            _serviceScopeFactory = serviceScopeFactory;
            _otpService = otpService;
            _configuration = configuration;
        }
        //api/Account/Registration
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<UserRegistrationDTO>>> Registration(UserRegistrationDTO dto)
        {
            var response = new ResponseDTO<UserRegistrationDTO> { StatusCode = ResponseCode.Error };

            try
            {
                // Step 1️⃣ Validate DTO
                var validation = dto.Validate();
                if (!validation.IsSuccessCode())
                {
                    return Ok(response.SetMessage(validation.Message));
                }

                // Step 3️⃣ Validate new user registration
                // Step 3️⃣ Validate new user registration
                var (emailAvailable, emailError, emailUser) = await _commonDBLogic.CheckEmailAvailabilityAsync(dto.Email);
                if (!emailAvailable)
                {
                    if (emailUser != null && !emailUser.IsEmailVerified)
                    {
                        return Ok(response.SetMessage(Resource.Email_NotVerified, ResponseCode.Phone_Not_Verified));
                    }

                    return Ok(response.SetMessage(emailError));
                }

                var (phoneAvailable, phoneError, phoneUser) = await _commonDBLogic.CheckPhoneAvailabilityAsync(dto.PhoneNumber, dto.DialCode);
                if (!phoneAvailable)
                {
                    if (phoneUser != null && !phoneUser.IsPhoneVerified)
                    {
                        return Ok(response.SetMessage(Resource.PhoneNumber_NotVerified, ResponseCode.Phone_Not_Verified));
                    }

                    return Ok(response.SetMessage(phoneError));
                }

                var country = await _context.Countries.FirstOrDefaultAsync(a => a.PhoneCode == dto.DialCode);
                var user = new User
                {
                    FirstName = dto.FirstName,
                    LastName = dto.LastName,
                    Email = dto.Email,
                    PhoneNumber = dto.PhoneNumber,
                    AddressLine1 = dto.AddressLine1,
                    DialCode = dto.DialCode,
                    CountryId = country != null ? country.Id : null,
                    State = dto.State,
                    City = dto.City,
                    ZipCode = dto.ZipCode,

                    CreatedAt = DateTimeHelper.GetUtcTime(),
                    UpdatedAt = DateTimeHelper.GetUtcTime(),
                    IsEmailVerified = false,   // default until verification
                    IsPhoneVerified = false    // default until verification
                };

                return Ok(response.SetSuccess());


            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }
            return Ok(response.SetMessage(Resource.ZafeAccountCreationError));

        }

        // api/Account/LoginUsernamePaasword
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<AccessTokenResponseDTO>>> LoginUsernamePassword(LoginDTO dto)
        {
            var response = new ResponseDTO<AccessTokenResponseDTO>().SetFailed();

            var validation = dto.ValidateLogin();
            if (!validation.IsSuccessCode())
                return Ok(response.SetMessage(validation.Message));

            var input = dto.ContactOrEmail.NormalizeInput();

            // Find user in database
            var (user, loginType, error) = await _commonDBLogic.GetAndValidateUserAsync(input, dto.DailCode);
            if (!string.IsNullOrEmpty(error))
                return Ok(response.SetMessage(error));

            // User not found, check TTLock username
            user ??= await _context.Users.FirstOrDefaultAsync(u => u.TTLockUsername == input);

            if (user == null)
                return Ok(response.SetMessage(Resource.InvalidUsernameOrPassword));

            var verificationResult = GetVerificationFailureResponse(user);

            if (verificationResult.Code != ResponseCode.Success)
            {
                return Ok(response.SetMessage(
                    verificationResult.Message,
                    verificationResult.Code
                ));
            }

            if (string.IsNullOrEmpty(user.TTLockUsername))
            {
                response.SetMessage("", ResponseCode.Password_Create_Page);
                return Ok(response);
            }
            string ttPwd = PasswordHelper.GenerateMd5ForTTLock(dto.Password);

            var token = await _ttLockHelper.GetAccessTokenAsync(user.TTLockUsername, ttPwd);

            if (!token.IsSuccessCode() || token.Data?.AccessToken == null)
                return Ok(response.SetMessage(token.Message));


            await UpdateUserLoginStateAsync(user, ttPwd, token.Data);
            response.Data = SetAuthData(user, token.Data);
            return Ok(response.SetSuccess());
        }

        //api/Account/CreatePassword
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<bool>>> CreatePassword(CreatePasswordDTO dto)
        {
            var response = new ResponseDTO<bool> { StatusCode = ResponseCode.Error };

            try
            {
                // Step 1️⃣ Validate DTO
                var validation = dto.Validate();
                if (!validation.IsSuccessCode())
                {
                    return Ok(response.SetMessage(validation.Message));
                }

                var input = dto.ContactOrEmail.NormalizeInput();

                // Find user in database
                var (user, loginType, error) = await _commonDBLogic.GetAndValidateUserAsync(input, dto.DialCode);
                if (!string.IsNullOrEmpty(error))
                    return Ok(response.SetMessage(error));

                if (user == null)
                {
                    return Ok(response.SetMessage(
                        Resource.UnauthorizedAccess,
                        ResponseCode.Error
                    ));
                }

                if (!string.IsNullOrEmpty(user.TTLockUsername))
                {
                    //reset password
                    return Ok(response.SetMessage(
                       Resource.Password_Already_Created
                   ));
                }

                // Step 5️⃣ Prepare for TTLock verification
                string ttlockPwd = PasswordHelper.GenerateMd5ForTTLock(dto.Password);
                // Step 7️⃣ If user not found in TTLock, register new
                var username = CommonLogic.GenerateUserName(user);

                var ttResponse = await _ttLockHelper.RegisterUserAsync(username, ttlockPwd);

                if (ttResponse.IsSuccessCode() && !string.IsNullOrEmpty(ttResponse.Data.Username))
                {
                    user.TTLockHashPassword = ttlockPwd;
                    user.TTLockUsername = ttResponse.Data.Username;

                    _context.Users.Add(user);
                    await _context.SaveChangesAsync();

                    var responseOtp = await SendOtpToUserAsync(user, LoginOtpDeliveryMethod.Email);
                    if (responseOtp.IsSuccessCode())
                        return Ok(response.SetSuccess(responseOtp.Message));

                    return Ok(response.SetMessage(responseOtp.Message, ResponseCode.Error));
                }
                else
                {
                    response.SetMessage(ttResponse.Message);
                }

                return Ok(response);
            }
            catch (Exception ex)
            {
                response.SetMessage(ex.Message);
            }

            return Ok(response);
        }

        //api/Account/ResetPassword
        [HttpPost]
        public async Task<ActionResult<ResponseDTO<string>>> ResetPassword(ResetPasswordDTO dto)
        {
            var response = new ResponseDTO<string>().SetFailed();

            // Step 1️⃣ DTO validation (password + repeat password)
            var validation = dto.Validate();
            if (!validation.IsSuccessCode())
                return Ok(validation);

            // Step 3️⃣ Get and validate user
            var (user, type, error) = await _commonDBLogic.GetAndValidateUserAsync(dto.ContactOrEmail, dto.DialCode);

            if (error != null)
                return Ok(response.SetMessage(error));

            if (user == null)
                return Ok(response.SetMessage(Resource.UnauthorizedAccess));

            // Step 4️⃣ OTP verification
            var verify = _otpService.VerifyOtp(
                user,
                dto.Otp,
               UserInputValidator.ValidateEmail(dto.ContactOrEmail, out string emailError) ? OtpActionType.Password_Reset_Email : OtpActionType.Password_Reset_Phone
            );

            if (!verify.IsSuccessCode())
                return Ok(response.SetMessage(verify.Message));

            // Step 5️⃣ Reset password in TTLock
            string username = user.TTLockUsername;
            string ttlockPassword = PasswordHelper.GenerateMd5ForTTLock(dto.Password);

            var apiRes = await _ttLockHelper.ResetPasswordAsync(username, ttlockPassword);

            if (!(apiRes?.IsSuccessCode() ?? false))
                return Ok(response.SetMessage(apiRes?.Message ?? Resource.SomethingWentWrong));

            // Step 6️⃣ Update local password
            user.TTLockHashPassword = ttlockPassword;
            user.UpdatedAt = DateTimeHelper.GetUtcTime();

            await _context.SaveChangesAsync();

            return Ok(response.SetSuccess());
        }

        private async Task UpdateUserLoginStateAsync(User user, string ttPwd, AccessTokenResponseDTO tokenData)
        {
            user.TTLockHashPassword = ttPwd;
            user.LastLogin = DateTimeHelper.GetUtcTime();
            _commonDBLogic.SaveAcccesAndRefreshToken(user, tokenData);
            await _context.SaveChangesAsync();
        }
        private AccessTokenResponseDTO SetAuthData(User user, AccessTokenResponseDTO token)
        {
            if (user == null) throw new ArgumentNullException(nameof(user));

            token.FullName = user.FullName;
            return token;
        }

        private (ResponseCode Code, string Message) GetVerificationFailureResponse(User user)
        {
            bool hasEmail = !string.IsNullOrWhiteSpace(user.Email);
            bool hasPhone = !string.IsNullOrWhiteSpace(user.PhoneNumber);

            bool emailNotVerified = hasEmail && !user.IsEmailVerified;
            bool phoneNotVerified = hasPhone && !user.IsPhoneVerified;

            if (emailNotVerified && phoneNotVerified)
            {
                return (
                    ResponseCode.Email_And_Phone_Not_Verified,
                    Resource.EmailAndPhoneVerificationRequired
                );
            }

            if (emailNotVerified)
            {
                return (
                    ResponseCode.Email_Not_Verified,
                    Resource.EmailVerificationRequired
                );
            }

            if (phoneNotVerified)
            {
                return (
                    ResponseCode.Phone_Not_Verified,
                    Resource.ContactVerificationRequired
                );
            }

            // Nothing to verify
            return (ResponseCode.Success, string.Empty);
        }

        private async Task<ResponseDTO<string>> SendOtpToUserAsync(User user, LoginOtpDeliveryMethod type)
        {
            var operation = type == LoginOtpDeliveryMethod.Email
                ? OtpActionType.Login_Email
                : OtpActionType.Login_Sms;

            var result = _otpService.SendOtp(user, operation);
            var response = new ResponseDTO<string>();

            return result.IsSuccessCode()
                ? response.SetMessage(type == LoginOtpDeliveryMethod.Email ? Resource.OneTimeCodeToEmail : Resource.OneTimeCodeToPhone, ResponseCode.Success)
                : response.SetMessage(type == LoginOtpDeliveryMethod.Email ? Resource.OTPNotSendToEmail : Resource.OTPNotSendToPhone);
        }
    }
}
