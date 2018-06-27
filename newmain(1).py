import cx_Oracle
from dateutil.relativedelta import relativedelta
from terminaltables import AsciiTable
import datetime
from abc import abstractmethod

class user:
    _fname = ""
    _lname = ""
    _address = ""
    _city = ""
    _state = ""
    _pincode = 0
    _custid = ""
    _pass = ""
    _bal = 0
    def __init__(self, fname, lname, address, city, state, pincode):
        self._fname = fname
        self._lname = lname
        self._address = address
        self._state = state
        self._city = city
        self._pincode = pincode
        
    def createuser(self, acctype):
        con = cx_Oracle.connect("bank/banksystem@XE")
        cur = con.cursor()
        if acctype == "Savings":
            cur.execute("SELECT CUSTID FROM CUSTOMER WHERE ACCTYPE = :1 ORDER BY CUSTID DESC",
                         (acctype,))
            ans = cur.fetchone()
            if ans == None:
                self._custid = "S1001"
            else:
                self._custid = ans[0][0] + str(int(ans[0][1:]) + 1)
            self._pass = input("Enter Password for your account: ")
            try:
                cur.execute("INSERT INTO CUSTOMER VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)",
                            (self._custid, self._pass, self._fname, self._lname, self._address, self._city,
                            self._state, self._pincode, acctype))
                
                self._bal = float(input("Enter starting balance(enter 0 for no starting balance): "))
                cur.execute("INSERT INTO ACCOUNTDETAILS VALUES (:1, :2, :3, :4)",
                            (self._custid, acctype, self._bal, datetime.date.today()))

            except cx_Oracle.DatabaseError:
                print("Invalid Entry!")
        elif acctype == "Current":
            cur.execute("SELECT CUSTID FROM CUSTOMER WHERE ACCTYPE = :1 ORDER BY CUSTID DESC",
                         (acctype,))
            ans = cur.fetchone()
            if ans == None:
                self._custid = "C1001"
            else:
                self._custid = ans[0][0] + str(int(ans[0][1:]) + 1)
            self._pass = input("Enter Password for your account: ")
            try:
                self._bal = float(input("Enter starting balance(Minimum 5000 required!): "))
                if(self._bal < 5000.0):
                    raise ValueError
                
                cur.execute("INSERT INTO CUSTOMER VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)",
                            (self._custid, self._pass, self._fname, self._lname, self._address, self._city,
                            self._state, self._pincode, acctype))
                cur.execute("INSERT INTO ACCOUNTDETAILS VALUES (:1, :2, :3, :4)",
                            (self._custid, acctype, self._bal, datetime.date.today()))

            except cx_Oracle.DatabaseError:
                print("Invalid Entry!")
            except ValueError:
                print("Not enough balance to open Current account!")
        con.commit()
        con.close()
        print("Customer added Successfully")
        print("Customer id: ",self._custid)
     
def verify(cid, pwd):
    con = cx_Oracle.connect("bank/banksystem@XE")
    cur = con.cursor()
    cur.execute("SELECT * FROM CUSTOMER WHERE CUSTID = :1 AND PASS = :2", (cid, pwd))
    ans = cur.fetchall()
    if len(ans) == 1:
        return True
    return False
          
class account:
    _custid = ""
    def __init__(self, cid):
        self._custid = cid
        self._con = cx_Oracle.connect("bank/banksystem@XE")
        self._cur = self._con.cursor()
        
    def verifypassword(self):
        self._verify = input("Enter password:")
        self._cur.execute("SELECT COUNT(*) FROM CUSTOMER WHERE CUSTID = :1 AND PASS = :2",
                    (self._custid, self._verify))
        ans = self._cur.fetchone()
        if ans[0] == 1:
            return True
        return False
        
    def addresschange(self):
        self._newadd = input("Enter new Address: ")
        if(self.verifypassword()):
            try:
                self._cur.execute("UPDATE CUSTOMER SET ADDRESS = :1 WHERE CUSTID = :2", (self._newadd, self._custid))
                self._con.commit()
            except cx_Oracle.DatabaseError:
                print("Operation Unsuccessful!")
        else:
            print("Invalid Password!")
                
    def deposit(self, bal):
        if(self.verifypassword()):
            try:
                self._cur.execute("SELECT BALANCE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                ans = self._cur.fetchone()
                before_bal = ans[0]
                self._cur.execute("INSERT INTO TRANSACTIONS VALUES (:1, :2, :3, :4, :5, :6, :7)",
                                   (self._custid, self._custid, "Deposit", datetime.date.today(), 
                                    bal, before_bal, before_bal + bal))
                self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = :1 WHERE ACCOUNTID = :2", (before_bal + bal, self._custid))
                self._con.commit()
                print("Deposit Successful!")
                print("New balance: ",before_bal + bal)
            except cx_Oracle.DatabaseError:
                print("Unsuccessful")
        else:
            print("Invalid Password!")
    
    @abstractmethod     
    def withdraw(self, bal):
        pass
    
    def printstatement(self):
        print("1. All transactions\n2. Specific Date range")
        sel = int(input("Choice: "))
        if(sel == 1):
            self._cur.execute("SELECT * FROM TRANSACTIONS WHERE ACCOUNTFROM = :1 OR ACCOUNTTO = :1", (self._custid,))
            ans = self._cur.fetchall()
        elif(sel == 2):
            datefrom = input("Enter Date from(YYYY-MM-DD): ")
            year, month, day = map(int, datefrom.split('-'))
            datefrom = datetime.date(year, month, day)
             
            dateto = input("Enter Date from(YYYY-MM-DD): ")
            year, month, day = map(int, dateto.split('-'))
            dateto = datetime.date(year, month, day) 
            
            self._cur.execute("SELECT * FROM TRANSACTIONS WHERE (ACCOUNTFROM = :1 OR ACCOUNTTO = :1) AND DATEOFTRANSACTION BETWEEN :2 AND :3",
                              (self._custid, datefrom, dateto))
            ans = self._cur.fetchall()
        else:
            print("Invalid Choice!")
        table_data = [['From Account', 'To Account', 'Description', 'Date', 'Amount', 'Before Balance', 'After balance']]
        for val in ans:
            table_data.append(val)
        table = AsciiTable(table_data, "Transactions")
        print(table.table)
        
    
    def transfermoney(self):
        accto = input("Enter Account ID of receiver: ")
        self._cur.execute("SELECT * FROM CUSTOMER WHERE CUSTID = :1", (accto,))
        ans = self._cur.fetchone()
        if ans != None:
            transferbal = float(input("Enter amount to transfer: "))
            self._cur.execute("SELECT BALANCE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
            val = self._cur.fetchone()[0]
            if val > transferbal:
                try:
                    self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = :1 WHERE ACCOUNTID = :2", (val - transferbal, self._custid))
                    self._cur.execute("INSERT INTO TRANSACTIONS VALUES (:1, :2, :3, :4, :5, :6, :7)",
                                   (self._custid, accto, "Transfer", datetime.date.today(), 
                                    transferbal, val, val - transferbal))
                    self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = BALANCE + :1 WHERE ACCOUNTID = :2", (transferbal, accto))
                    self._con.commit()
                    print("Transfer Successful!")
                except cx_Oracle.DatabaseError as e:
                    print(e)
                    print("Transfer Unsuccessful!")
            else:
                print("Not Enough Money!")
        else:
            print("Invalid Account ID!")
        
        pass
    
    def accountclosure(self):
        val = input("Are you Sure? (Y/N): ")
        if(val.lower() == 'y'):
            if(self.verifypassword()):
                try:
                    self._cur.execute("SELECT FIRSTNAME, LASTNAME FROM CUSTOMER WHERE CUSTID = :1", (self._custid,))
                    ans = self._cur.fetchall()
                    name = ans[0][0] + " " + ans[0][1]
                    self._cur.execute("INSERT INTO CLOSEDACCOUNTS VALUES (:1, :2, :3)", 
                                      (self._custid, datetime.date.today(), name))
                    self._cur.execute("DELETE FROM TRANSACTIONS WHERE ACCOUNTFROM = :1", (self._custid,))
                    self._cur.execute("SELECT * FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                    
                    self._cur.execute("DELETE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                    self._cur.execute("DELETE FROM CUSTOMER WHERE CUSTID = :1", (self._custid,))
                    self._con.commit()
                    print(ans)
                    print("Delete Successful!")
                except cx_Oracle.DatabaseError as e:
                    print(e)
                    print("Delete Unsuccessful!")
            else:
                print("Invalid Password!")
                
    def __del__(self):
        self._con.close()
             
class savings(account):
    def checkwithdraw(self):
        today = datetime.date.today()
        mon_first = datetime.date(today.year, today.month, 1)
        self._cur.execute("SELECT COUNT(*) FROM TRANSACTIONS WHERE ACCOUNTFROM = :1 AND (DESCRIP = 'Withdraw' OR DESCRIP = 'Transfer') AND  DATEOFTRANSACTION BETWEEN :2 AND :3",
                          (self._custid, mon_first, today))
        ans = self._cur.fetchall()
        if(ans[0][0] <= 10):
            return True
        return False
    
    @abstractmethod
    def withdraw(self, bal):
        self.checkwithdraw()
        if(self.verifypassword()):
            try:
                self._cur.execute("SELECT BALANCE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                ans = self._cur.fetchone()
                before_bal = ans[0]
                if(before_bal - bal < 0):
                    print("Insufficient Balance!")
                    return
                self._cur.execute("INSERT INTO TRANSACTIONS VALUES (:1, :2, :3, :4, :5, :6, :7)",
                                   (self._custid, self._custid, "Withdraw", datetime.date.today(), 
                                    bal, before_bal, before_bal - bal))
                self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = :1 WHERE ACCOUNTID = :2", (before_bal - bal, self._custid))
                self._con.commit()
                print("Withdraw Successful!")
                print("New balance: ",before_bal - bal)
            except cx_Oracle.DatabaseError:
                print("Unsuccessful")
        else:
            print("Invalid Password!")
            
    def interest(self):
        self._cur.execute("""SELECT DATEOFTRANSACTION FROM TRANSACTIONS WHERE DESCRIP = 'Interest' AND ACCOUNTFROM = :1 
                            ORDER BY DATEOFTRANSACTION DESC""", (self._custid,))
        ans = self._cur.fetchone()
        if(ans == None):
            self._cur.execute("SELECT OPENINGDATE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
            ans = self._cur.fetchone()
            val = relativedelta(datetime.date.today(), ans[0])
            if(val.years == 1 and val.days == 0):
                try:
                    self._cur.execute("SELECT BALANCE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                    ans = self._cur.fetchone()
                    before_bal = ans[0]
                    self._cur.execute("INSERT INTO TRANSACTIONS VALUES (:1, :2, :3, :4, :5, :6, :7)",
                                               (self._custid, self._custid, "Interest", datetime.date.today(), 
                                                0.75 * before_bal, before_bal, before_bal + 0.75 * before_bal))
                    self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = :1 WHERE ACCOUNTID = :2", (before_bal + 0.75 * before_bal, self._custid))
                    self._con.commit()
                except cx_Oracle.DatabaseError as e:
                    print(e)
        else:
            val = relativedelta(datetime.date.today(), ans[0])
            if(val.years == 1 and val.days == 0):
                try:
                    self._cur.execute("SELECT BALANCE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                    ans = self._cur.fetchone()
                    before_bal = ans[0]
                    self._cur.execute("INSERT INTO TRANSACTIONS VALUES (:1, :2, :3, :4, :5, :6, :7)",
                                           (self._custid, self._custid, "Interest", datetime.date.today(), 
                                            0.75 * before_bal, before_bal, before_bal + 0.75 * before_bal))
                    self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = :1 WHERE ACCOUNTID = :2", (before_bal + 0.75 * before_bal, self._custid))
                    self._con.commit()
                except cx_Oracle.DatabaseError as e:
                    print(e)
                
class current(account):
    @abstractmethod
    def withdraw(self, bal):
        if(self.verifypassword()):
            try:
                self._cur.execute("SELECT BALANCE FROM ACCOUNTDETAILS WHERE ACCOUNTID = :1", (self._custid,))
                ans = self._cur.fetchone()
                before_bal = ans[0]
                if(before_bal - bal < 5000.0):
                    print("Withdraw Not allowed!")
                    return
                self._cur.execute("INSERT INTO TRANSACTIONS VALUES (:1, :2, :3, :4, :5, :6, :7)",
                                   (self._custid, self._custid, "Withdraw", datetime.date.today(), 
                                    bal, before_bal, before_bal - bal))
                self._cur.execute("UPDATE ACCOUNTDETAILS SET BALANCE = :1 WHERE ACCOUNTID = :2", (before_bal - bal, self._custid))
                self._con.commit()
                print("Withdraw Successful!")
                print("New balance: ",before_bal - bal)
            except cx_Oracle.DatabaseError:
                print("Unsuccessful")
        else:
            print("Invalid Password!")

if __name__ == '__main__':
    while(1):
        print("1. Sign Up (New Customer) \n2. Sign In (Existing Customer) \n3. Admin Sign In \n4. Quit")
        choice = int(input("Choice: "))
        if choice == 1:
            Fname = input("Enter First name: ")
            Lname = input("Enter Last name: ")
            Address = input("Enter your address: ")
            city = input("Enter your city: ")
            state = input("Enter State: ")
            pincode = int(input("Enter PIN code: "))
            cust = user(Fname, Lname, Address, city, state, pincode)
            atype = input("Enter Account Type: ")
            cust.createuser(atype)
            del(cust)
            
        elif choice == 2:
            count = 0
            custid = input("Enter your customer id: ")
            while(count != 3):
                passwd = input("Enter your Password: ")
                if(verify(custid, passwd)):
                    count = 3
                    if(custid[0] == 'S'):
                        acc = savings(custid)
                        acc.interest()
                    else:
                        acc = current(custid)
                    
                    while(True):
                        print("""1. Address Change\n2. Money Deposit\n3. Money Withdrawal\n4. Print Statement\n5. Transfer Money\n6. Account Closure\n7. Logout""")
                        choice = int(input("Choice: "))
                        if(choice == 1):
                            acc.addresschange()
                        elif(choice == 2):
                            dep_balance = float(input("Enter Balance to Deposit: "))
                            acc.deposit(dep_balance)
                        elif(choice == 3):
                            with_balance = float(input("Enter Balance to Withdraw: "))
                            acc.withdraw(with_balance)
                        elif(choice == 4):
                            acc.printstatement()
                        elif(choice == 5):
                            acc.transfermoney()
                        elif(choice == 6):
                            acc.accountclosure()
                            del(acc)
                            break
                        elif(choice == 7):
                            del(acc)
                            break
                        else:
                            print("Invalid Choice!")
                else:
                    print("Invalid Customer ID or Password!")
                    count += 1
                    if(count < 3):
                        print("Try Again!")
                    else:
                        print("Maximum try limit Expired!")
                
        elif choice == 3:
            adminid = input("Enter Admin ID: ")
            count = 0
            while(count != 3):
                pwd = input("Enter Password: ")
                try:
                    con = cx_Oracle.connect("bank/banksystem@XE")
                    cur = con.cursor()
                    cur.execute("SELECT * FROM ADMINDETAILS WHERE ADMINID = :1 AND PASSWD = :2",
                                (adminid, pwd))
                    ans = cur.fetchall()
                    if len(ans) == 1:
                        count = 3
                        print("Welcome")
                        while(True):
                            print("1. Closed Account History\n2. Logout")
                            choice = int(input("Choice: "))
                            if(choice == 1):
                                cur.execute("SELECT * FROM CLOSEDACCOUNTS")
                                table_data = [['Account ID', 'Date of closure', 'Account holder Name']]
                                ans = cur.fetchall()
                                for val in ans:
                                    table_data.append(val)
                                table = AsciiTable(table_data, "Closed Accounts")
                                print(table.table)
                            elif(choice == 2):
                                break
                            else:
                                print("Invalid Choice!")
                    else:
                        print("Invalid Details!")
                        count += 1
                        if(count < 3):
                            print("Try Again!")
                        else:
                            print("Maximum Try limit Expired!")
                except cx_Oracle.DatabaseError as e:
                    print(e)
                
        elif choice == 4:
            break;
        else:
            print("Invalid Choice!")
