using Resido.Model.CommonDTO;
using Resido.Resources;

namespace Resido.Model.AuthDTO
{
    public class LoginDTO: ContactOrEmailDTO
    {
        public string? DailCode { get; set; }
        public string? Password { get; set; }
        public ResponseDTO<string> ValidateLogin()
        {
            ResponseDTO<string> responseDTO = new ResponseDTO<string>();
            responseDTO.SetFailed();

            if (string.IsNullOrWhiteSpace(ContactOrEmail))
                return responseDTO.SetMessage(Resource.ContactOrEmail_Required);

            if (string.IsNullOrWhiteSpace(Password))
                return responseDTO.SetMessage(Resource.Password_Required);

            return responseDTO.SetSuccess();
        }
    }
    public class ContactOrEmailDTO
    {
        public string? DialCode { get; set; }
        public string? ContactOrEmail { get; set; }
    }

}
