using Resido.Model;
using Resido.Model.CommonDTO;
using Resido.Resources;

namespace Resido.Helper.EmailHelper
{
    public class EmailResponseModel
    {
        public string Body { get; set; }
    }
    public class MailHelper
    {
        public async static Task<ResponseDTO<string>> SendEmailAsync(MailRequestModel mailRequest)
        {
            ResponseDTO<string> response = new ResponseDTO<string>();
            response.StatusCode = ResponseCode.Error;
            try
            {
                response.SetSuccess();
                //response = await SendGridAPIHelper.SendEmailAsync(mailRequest.ToEmail, mailRequest.Subject, mailRequest.Body);
                mailRequest.Body += "<br><br>" + Resource.EmailBestRegards + "<br>" + Resource.EmailTeam;
                response = await GoogleEmailService.SendEmail(mailRequest.ToEmail, mailRequest.Subject, mailRequest.Body);
            }
            catch (Exception ex)
            {
                response.Message = ex.Message;
            }
            return response;
        }
        public async static Task<ResponseDTO<string>> SendEmailCustomAsync(MailRequestModel mailRequest)
        {
            ResponseDTO<string> response = new ResponseDTO<string>();
            response.StatusCode = ResponseCode.Error;
            try
            {
                response.SetSuccess();
                response = await GoogleEmailService.SendEmail(mailRequest.ToEmail, mailRequest.Subject, mailRequest.Body);
            }
            catch (Exception ex)
            {
                response.Message = ex.Message;
            }
            return response;
        }

    }
}
