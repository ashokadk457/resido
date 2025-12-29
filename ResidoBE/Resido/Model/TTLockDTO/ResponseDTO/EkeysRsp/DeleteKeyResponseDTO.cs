namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    public class DeleteKeyResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
