using Resido.Helper;
using Resido.Model.CommonDTO;
using Resido.Resources;

namespace Resido.Model.AuthDTO
{
    public class UserRegistrationDTO
    {
        public string FirstName { get; set; }
        public string? LastName { get; set; }
        public string Email { get; set; }
        public string PhoneNumber { get; set; }
        public string? AddressLine1 { get; set; }
        public string DialCode { get; set; }
        public string? Country { get; set; }
        public string? State { get; set; }
        public string? City { get; set; }
        public string? ZipCode { get; set; }
        public ResponseDTO<string> Validate()
        {
            var responseDTO = new ResponseDTO<string>();
            responseDTO.SetFailed();

            if (!UserInputValidator.ValidateEmail(Email, out string emailError))
                return responseDTO.SetMessage(emailError);

            if (!UserInputValidator.ValidatePhoneNumber(PhoneNumber, out string phoneError))
                return responseDTO.SetMessage(phoneError);

            if (!UserInputValidator.ValidateDialCode(DialCode, out string dialError))
                return responseDTO.SetMessage(dialError);


            return responseDTO.SetSuccess();
        }
    }
}
