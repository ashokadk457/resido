using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper;
using Resido.Helper.EmailHelper;
using Resido.Model;
using Resido.Model.CommonDTO;
using Resido.Resources;
using static Resido.Services.SmsDkService;

namespace Resido.Services.DAL
{
    public class OtpService
    {
        ResidoDbContext _context;
        SmsDkService _smsDkService;
        private readonly ILogger _logger;
        public OtpService(ResidoDbContext context, ILogger<OtpService> logger, SmsDkService smsDkService)
        {
            _context = context;
            _logger = logger;
            _smsDkService = smsDkService;
        }
        #region Public Methods
        public ResponseDTO<string> SendOtp(User user, OtpActionType operationType)
        {
            return HandleOtp(user, operationType, null, null);
        }

        public ResponseDTO<string> SendUpdateOtp(User user, OtpActionType operationType, EmailDTO emailDTO, PhoneDTO phoneDTO)
        {
            return HandleOtp(user, operationType, emailDTO, phoneDTO);
        }
        internal ResponseDTO<string> VerifyOtp(User user, string otp, OtpActionType operationType)
        {
            ResponseDTO<string> response = new ResponseDTO<string>();
            response.StatusCode = ResponseCode.Error;

            var otpkey = UserParameterKey.Otp;
            var sendTimeKey = UserParameterKey.Otp_Send_Time;
            if (user.UserParameter?.Any() ?? false)
            {
                switch (operationType)
                {
                    case OtpActionType.Login_Sms:
                    case OtpActionType.Login_Email:
                        sendTimeKey = UserParameterKey.Otp_Send_Time;
                        otpkey = UserParameterKey.Otp;
                        break;
                    case OtpActionType.Password_Reset_Email:
                    case OtpActionType.Password_Reset_Phone:
                        sendTimeKey = UserParameterKey.Password_Reset_Otp_Send_Time;
                        otpkey = UserParameterKey.Password_Reset_Otp;
                        break;
                }
                var otpValue = CommonLogic.GetUserParamValue(user.UserParameter, otpkey);
                var otpSendTime = CommonLogic.GetUserParamValue(user.UserParameter, sendTimeKey);
                if (string.IsNullOrEmpty(otp) || string.IsNullOrEmpty(otpSendTime))
                {
                    response.SetMessage(Resource.SendOtpBeforeVerification);//Otp not send
                    return response;
                }

                var sendTime = new DateTime(Convert.ToInt64(otpSendTime));
                if ((DateTimeHelper.GetUtcTime() - sendTime).TotalMinutes > 50)
                {
                    //Otp expired
                    response.SetMessage(Resource.OneTimePassword);
                    return response;
                }

                if (!string.IsNullOrEmpty(otpValue) && otpValue == otp)
                {
                    response.StatusCode = ResponseCode.Success;

                    //Set all values to empty
                    bool isClearKey = false;
                    switch (operationType)
                    {
                        case OtpActionType.Login_Sms:
                        case OtpActionType.Login_Email:
                        case OtpActionType.Password_Reset_Phone:
                        case OtpActionType.Password_Reset_Email:
                        case OtpActionType.Update_Email:
                        case OtpActionType.Update_Phone:
                            isClearKey = true;
                            break;
                    }
                    if (isClearKey)
                    {
                        response.StatusCode = ResponseCode.Success;

                        if (operationType != OtpActionType.Password_Reset_Email && operationType != OtpActionType.Password_Reset_Phone)
                        {
                            user.UserParameter = CommonLogic.UpdateUserParameter(user.UserParameter, otpkey, "");
                            user.UserParameter = CommonLogic.UpdateUserParameter(user.UserParameter, sendTimeKey, "");
                        }
                    }
                    _context.SaveChanges();
                    return response;
                }
                else
                {
                    //Invalid Otp
                    response.SetMessage(Resource.InvalidOtp);
                    return response;
                }
            }
            else
            {
                //Otp not send
                response.SetMessage(Resource.SendOtpBeforeVerification);
                return response;
            }
        }
        #endregion

        #region Core Handler
        private ResponseDTO<string> HandleOtp(User user, OtpActionType operationType, EmailDTO emailDTO, PhoneDTO phoneDTO)
        {
            var response = new ResponseDTO<string>();
            response.SetFailed();

            if (user.UserParameter == null)
                user.UserParameter = new List<UserParameter>();

            // Resolve keys
            var (otpKey, sendTimeKey) = ResolveKeys(operationType);

            // Check resend policy
            if (!CanResendOtp(user, sendTimeKey))
            {
                response.SetMessage(string.Format(Resource.ResentOtpAfterTime, ApplicationDefaults.resendSeconds));
                return response;
            }

            if (phoneDTO != null && !string.IsNullOrEmpty(phoneDTO.ContactNo))
            {
                user.UserParameter = CommonLogic.UpsertUserParameter(user.UserParameter, UserParameterKey.New_Dial_Code_To_Update, phoneDTO.DialCode);
                user.UserParameter = CommonLogic.UpsertUserParameter(user.UserParameter, UserParameterKey.New_Phone_To_Update, phoneDTO.ContactNo);
            }
            if (emailDTO != null && !string.IsNullOrEmpty(emailDTO.Email))
            {
                user.UserParameter = CommonLogic.UpsertUserParameter(user.UserParameter, UserParameterKey.New_Email_To_Update, emailDTO.Email);
            }
            // Generate and store OTP
            var otp = GenerateAndStoreOtp(user, otpKey, sendTimeKey);

            // Handle SMS / Email
            switch (operationType)
            {
                case OtpActionType.Login_Sms:
                case OtpActionType.Password_Reset_Phone:
                case OtpActionType.Update_Phone:
                    return SendSmsOtp(user, phoneDTO, otp, BuildSmsBody(operationType, otp), "HandleOtp");

                case OtpActionType.Login_Email:
                case OtpActionType.Password_Reset_Email:
                case OtpActionType.Update_Email:
                    return SendEmailOtp(user, emailDTO, otp, BuildEmailSubject(operationType), BuildEmailBody(operationType, otp), "HandleOtp");

                default:
                    response.SetMessage(Resource.InvalidOtpSendingMedium);
                    return response;
            }
        }
        #endregion

        #region Helpers
        private (UserParameterKey otpKey, UserParameterKey sendTimeKey) ResolveKeys(OtpActionType operationType)
        {
            return operationType switch
            {
                OtpActionType.Password_Reset_Email => (UserParameterKey.Password_Reset_Otp, UserParameterKey.Password_Reset_Otp_Send_Time),
                OtpActionType.Password_Reset_Phone => (UserParameterKey.Password_Reset_Otp, UserParameterKey.Password_Reset_Otp_Send_Time),
                OtpActionType.Update_Phone => (UserParameterKey.Phone_Update_Otp, UserParameterKey.Phone_Update_Otp_Send_Time),
                _ => (UserParameterKey.Otp, UserParameterKey.Otp_Send_Time)
            };
        }

        private bool CanResendOtp(User user, UserParameterKey sendTimeKey)
        {
            var otpSendTime = CommonLogic.GetUserParamValue(user.UserParameter, sendTimeKey);
            if (!string.IsNullOrEmpty(otpSendTime))
            {
                var lastOtpSendTime = new DateTime(Convert.ToInt64(otpSendTime));
                return (DateTime.UtcNow - lastOtpSendTime).TotalSeconds > ApplicationDefaults.resendSeconds;
            }
            return true;
        }

        private string GenerateAndStoreOtp(User user, UserParameterKey otpKey, UserParameterKey sendTimeKey)
        {
            var otp = CommonLogic.Generateneotp();

            user.UserParameter = CommonLogic.UpsertUserParameter(user.UserParameter, otpKey, otp);
            user.UserParameter = CommonLogic.UpsertUserParameter(user.UserParameter, sendTimeKey, DateTime.UtcNow.Ticks.ToString());

            return otp;
        }

        private ResponseDTO<string> SendSmsOtp(User user, PhoneDTO phoneDTO, string otp, string body, string source)
        {
            var response = new ResponseDTO<string>();
            SMSSenderModal sms = new()
            {
                PhonePrefex = phoneDTO != null ? phoneDTO.DialCode : user.DialCode,
                PhoneReciever = phoneDTO != null ? phoneDTO.ContactNo : user.PhoneNumber,
                Body = body
            };

            var result = _smsDkService.SendSmsAsync(new SmsRequestDto
            {
                Receiver = $"{sms.PhonePrefex}{sms.PhoneReciever}",
                Message = sms.Body
            }).Result;

            if (result.IsSuccessCode())
            {
                response.SetSuccess();
                response.Message = Resource.OtpSend;
            }
            else
            {
                response.SetFailed();
                response.Message = result.Message ?? Resources.Resource.SomethingWentWrong;
            }

            return response;
        }

        private ResponseDTO<string> SendEmailOtp(User user, EmailDTO emailDTO, string otp, string subject, string body, string source)
        {
            var response = new ResponseDTO<string>();
            MailRequestModel mail = new()
            {
                ToEmail = emailDTO != null ? emailDTO.Email : user.Email,
                Subject = subject,
                Body = body
            };


            var result = MailHelper.SendEmailAsync(mail).Result;

            if (result.IsSuccessCode())
            {
                response.SetSuccess();
                response.Message = Resource.OtpSendEmail;
                _context.SaveChanges();
            }
            else
            {
                response.SetFailed();
                response.Message = Resource.SomethingWentWrong;
            }

            return response;
        }


        private string BuildSmsBody(OtpActionType op, string otp) =>
            op switch
            {
                OtpActionType.Update_Phone => string.Format(Resource.UpdateUserPhone, otp),
                OtpActionType.Login_Sms => string.Format(Resource.SmsBody, otp),
                _ => string.Format(Resource.UpdatePasswordOtp, otp)
            };

        private string BuildEmailSubject(OtpActionType op) =>
            op switch
            {
                OtpActionType.Update_Email => Resource.ZafeLockEmailUpdateOTP,
                OtpActionType.Login_Email => Resource.SubjectVerifyEmail,
                _ => Resource.ResetPasswordSubject
            };

        private string BuildEmailBody(OtpActionType op, string otp) =>
            op switch
            {
                OtpActionType.Update_Email => string.Format(Resource.UpdateEmailOtp, otp),
                OtpActionType.Login_Email => string.Format(Resource.SmsBody, otp),
                _ => string.Format(Resource.UpdatePasswordOtp, otp)
            };
        #endregion
    }
}
