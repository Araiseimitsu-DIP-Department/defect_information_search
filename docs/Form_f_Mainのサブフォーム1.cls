Option Compare Database
Option Explicit

'品番がクリックされた
Private Sub 品番_Click()
    If Not IsNull(Me.品番) Then
        Forms("f_Main").ClearDisp
        Forms("f_Main").txtHinban = Me.品番
        Forms("f_Main").GoukeiDisp              '合計表示
    End If
End Sub