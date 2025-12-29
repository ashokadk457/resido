using Resido.Resources;
using System.Resources;

namespace Resido.Model.CommonDTO
{
    public enum ResponseCode
    {
        Success = 0,
        Error = 1,
        Permission_Denied = 2,
        Email_Not_Verified = 3,
        Phone_Not_Verified = 4,
        Sms_Send_Failure = 5,
        Password_Create_Page = 6,
        Email_And_Phone_Not_Verified = 7,

    }
    public class ResponseDTO<T>
    {
        public ResponseCode StatusCode { get; set; }
        public string? Message { get; set; }
        public T? Data { get; set; }

        public ResponseDTO<T> SetMessage(string? message, ResponseCode responseCode = ResponseCode.Error)
        {
            StatusCode = responseCode;
            Message = message;
            return this;
        }
        public void SetMessageUnAuthorize()
        {
            StatusCode = ResponseCode.Permission_Denied;
            Message = Resource.UnauthorizedAccess;
        }
        public ResponseDTO<T> SetSuccess(string? message = "")
        {
            StatusCode = ResponseCode.Success;
            Message = message;
            return this;
        }
        public ResponseDTO<T> SetFailed(string? message = "")
        {
            StatusCode = ResponseCode.Error;
            Message = message;
            return this;
        }
        public bool IsSuccessCode()
        {
            return StatusCode == ResponseCode.Success ? true : false;
        }
    }
}
