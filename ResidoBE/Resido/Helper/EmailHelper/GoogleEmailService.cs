using Resido.Model.CommonDTO;
using System.Net;
using System.Net.Mail;

namespace Resido.Helper.EmailHelper
{
    public class GoogleEmailService
    {
        private readonly static string _gmailUser = "ashok.patel@adequateinfosoft.co";
        private readonly static string _gmailAppPassword = "crtj ebmn olvf yafz"; // 16-char app password from Gmail

        public static async Task<ResponseDTO<string>> SendEmail(string toEmail, string subject, string body)
        {
            ResponseDTO<string> responseDTO = new ResponseDTO<string>();
            responseDTO.SetFailed();

            try
            {
                var fromAddress = new MailAddress(_gmailUser, "Zafe");
                var toAddress = new MailAddress(toEmail);

                using (var smtp = new SmtpClient
                {
                    Host = "smtp.gmail.com",
                    Port = 587,
                    EnableSsl = true,
                    DeliveryMethod = SmtpDeliveryMethod.Network,
                    UseDefaultCredentials = false,
                    Credentials = new NetworkCredential(_gmailUser, _gmailAppPassword)
                })
                using (var message = new MailMessage(fromAddress, toAddress)
                {
                    Subject = subject,
                    Body = body,
                    IsBodyHtml = true
                })
                {
                    await smtp.SendMailAsync(message);
                }

                responseDTO.SetSuccess();
            }
            catch (Exception ex)
            {
                responseDTO.SetFailed(ex.Message);
            }

            return responseDTO;
        }
    }
}
