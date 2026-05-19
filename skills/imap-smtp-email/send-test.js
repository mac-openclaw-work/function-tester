const nodemailer = require('nodemailer');
const t = nodemailer.createTransport({
  host: 'smtp.139.com',
  port: 465,
  secure: true,
  auth: { user: 'zonkiddshao@139.com', pass: '417549afb31c46c65400' }
});
t.sendMail({
  from: 'zonkiddshao@139.com',
  to: 'zonkiddshao@139.com',
  subject: '【function-tester】邮箱配置测试',
  text: '你好，这是来自 function-tester agent 的测试邮件。如果收到请回复确认。'
}, (e, i) => e ? console.error('E:', e.message) : console.log('OK:', i.messageId));