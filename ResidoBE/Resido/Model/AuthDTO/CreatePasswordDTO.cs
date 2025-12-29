using Resido.Helper;
using Resido.Model.CommonDTO;
using Resido.Resources;

namespace Resido.Model.AuthDTO
{
    public class CreatePasswordDTO : ContactOrEmailDTO
    {
        public string Password { get; set; }
        public string RepeatPassword { get; set; }
        public ResponseDTO<string> Validate()
        {
            ResponseDTO<string> responseDTO = new ResponseDTO<string>();
            responseDTO.SetFailed();

            if (string.IsNullOrWhiteSpace(ContactOrEmail))
                return responseDTO.SetMessage(Resource.ContactOrEmail_Required);

            if (string.IsNullOrWhiteSpace(Password))
                return responseDTO.SetMessage(Resource.Password_Required);

            if (string.IsNullOrWhiteSpace(RepeatPassword))
                return responseDTO.SetMessage(Resource.RepeatPassword_Required);

            if (!Password.Equals(RepeatPassword))
                return responseDTO.SetMessage(Resource.Password_Not_Match);

            if (!UserInputValidator.ValidatePassword(Password, out string passwordError))
                return responseDTO.SetMessage(passwordError);

            return responseDTO.SetSuccess();
        }
    }
}
