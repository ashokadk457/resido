namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    public class UnfreezeKeyResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
